//! Core fraud-scoring logic, kept separate from `main.rs` so it is unit-testable.
//!
//! The score is a deterministic heuristic in the range 0..=100. Higher means
//! riskier. The verdict bands match the rest of the system:
//!   0..=30   Low Risk    (green)
//!   31..=70  Medium Risk (amber)
//!   71..=100 High Risk   (red)

use serde::{Deserialize, Serialize};

/// Transaction as received from the Node worker (a subset of the API payload).
#[derive(Debug, Clone, Deserialize)]
pub struct Txn {
    pub amount: f64,
    #[serde(default)]
    pub location: String,
    #[serde(default)]
    pub card_type: String,
    /// ISO-8601 timestamp, e.g. "2026-06-17T10:30:00Z".
    #[serde(default)]
    pub timestamp: String,
}

/// The scoring result the engine prints as JSON on stdout.
#[derive(Debug, Clone, Serialize, PartialEq)]
pub struct Scored {
    pub score: u8,
    pub verdict: String,
    pub factors: Vec<String>,
}

/// Map a 0..=100 score to its verdict band.
pub fn verdict_for(score: u8) -> &'static str {
    if score <= 30 {
        "Low Risk"
    } else if score <= 70 {
        "Medium Risk"
    } else {
        "High Risk"
    }
}

/// Extract the hour (0..=23) from an ISO-8601 timestamp like
/// "2026-06-17T10:30:00Z". Returns `None` if it cannot be parsed.
pub fn hour_from_timestamp(ts: &str) -> Option<u32> {
    let time_part = ts.split('T').nth(1)?;
    let hh = time_part.get(0..2)?;
    hh.parse::<u32>().ok().filter(|h| *h < 24)
}

/// Compute the fraud score and verdict for a transaction.
///
/// Weights (capped, then clamped to 0..=100):
///  - amount: 1 risk point per $100, capped at 50
///  - unknown/empty location: +20
///  - prepaid card: +15
///  - odd-hour transaction (before 06:00 or at/after 23:00): +15
pub fn score_transaction(txn: &Txn) -> Scored {
    let mut score = 0.0_f64;
    let mut factors: Vec<String> = Vec::new();

    let amount_pts = (txn.amount.max(0.0) / 100.0).min(50.0);
    if amount_pts > 0.0 {
        factors.push(format!("amount ${:.2} (+{:.0})", txn.amount, amount_pts));
    }
    score += amount_pts;

    let loc = txn.location.trim();
    if loc.is_empty() || loc.eq_ignore_ascii_case("unknown") {
        score += 20.0;
        factors.push("unknown location (+20)".to_string());
    }

    if txn.card_type.eq_ignore_ascii_case("prepaid") {
        score += 15.0;
        factors.push("prepaid card (+15)".to_string());
    }

    if let Some(hour) = hour_from_timestamp(&txn.timestamp) {
        if hour < 6 || hour >= 23 {
            score += 15.0;
            factors.push(format!("odd-hour {:02}:00 (+15)", hour));
        }
    }

    let score = score.clamp(0.0, 100.0).round() as u8;
    Scored {
        score,
        verdict: verdict_for(score).to_string(),
        factors,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn txn(amount: f64, location: &str, card: &str, ts: &str) -> Txn {
        Txn {
            amount,
            location: location.into(),
            card_type: card.into(),
            timestamp: ts.into(),
        }
    }

    #[test]
    fn low_risk_small_normal_transaction() {
        let s = score_transaction(&txn(10.0, "NYC", "credit", "2026-06-17T12:00:00Z"));
        assert_eq!(s.verdict, "Low Risk");
        assert!(s.score <= 30);
    }

    #[test]
    fn high_risk_large_unknown_prepaid_oddhour() {
        let s = score_transaction(&txn(9000.0, "unknown", "prepaid", "2026-06-17T03:00:00Z"));
        assert_eq!(s.verdict, "High Risk");
        assert!(s.score >= 71);
    }

    #[test]
    fn amount_points_are_capped_at_50() {
        // $1,000,000 would be 10,000 points without the cap.
        let s = score_transaction(&txn(1_000_000.0, "NYC", "credit", "2026-06-17T12:00:00Z"));
        assert!(s.score <= 50, "amount alone must not exceed the 50-pt cap, got {}", s.score);
    }

    #[test]
    fn verdict_bands_are_correct() {
        assert_eq!(verdict_for(0), "Low Risk");
        assert_eq!(verdict_for(30), "Low Risk");
        assert_eq!(verdict_for(31), "Medium Risk");
        assert_eq!(verdict_for(70), "Medium Risk");
        assert_eq!(verdict_for(71), "High Risk");
        assert_eq!(verdict_for(100), "High Risk");
    }

    #[test]
    fn hour_parsing() {
        assert_eq!(hour_from_timestamp("2026-06-17T03:30:00Z"), Some(3));
        assert_eq!(hour_from_timestamp("2026-06-17T23:00:00Z"), Some(23));
        assert_eq!(hour_from_timestamp("not-a-date"), None);
    }

    #[test]
    fn empty_location_treated_as_unknown() {
        let s = score_transaction(&txn(0.0, "", "credit", "2026-06-17T12:00:00Z"));
        assert!(s.factors.iter().any(|f| f.contains("unknown location")));
    }
}
