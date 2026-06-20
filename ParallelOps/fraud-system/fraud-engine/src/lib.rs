use serde::{Deserialize, Serialize};

#[derive(Debug, Deserialize)]
pub struct Txn {
    pub amount: f64,
    #[serde(default)]
    pub location: String,
    #[serde(default)]
    pub card_type: String,
    pub timestamp: String,
}

#[derive(Debug, Serialize)]
pub struct ScoreResult {
    pub score: u8,
    pub verdict: String,
    pub factors: Vec<String>,
}

fn hour_from_iso(ts: &str) -> u32 {
    ts.split('T')
        .nth(1)
        .and_then(|t| t.get(0..2))
        .and_then(|h| h.parse::<u32>().ok())
        .unwrap_or(12)
}

pub fn score_transaction(t: &Txn) -> ScoreResult {
    let mut s = 0.0_f64;
    let mut factors: Vec<String> = Vec::new();

    let amt_pts = (t.amount / 100.0).min(50.0);
    s += amt_pts;
    if t.amount >= 3000.0 {
        factors.push("large_amount".into());
    }

    if t.location.eq_ignore_ascii_case("unknown") {
        s += 20.0;
        factors.push("unknown_location".into());
    }
    if t.card_type.eq_ignore_ascii_case("prepaid") {
        s += 15.0;
        factors.push("prepaid_card".into());
    }
    let hour = hour_from_iso(&t.timestamp);
    if hour < 6 || hour >= 23 {
        s += 15.0;
        factors.push("odd_hour".into());
    }

    let score = s.clamp(0.0, 100.0) as u8;
    let verdict = if score <= 30 {
        "Low Risk"
    } else if score <= 70 {
        "Medium Risk"
    } else {
        "High Risk"
    };

    ScoreResult {
        score,
        verdict: verdict.to_string(),
        factors,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn txn(amount: f64, loc: &str, card: &str, ts: &str) -> Txn {
        Txn {
            amount,
            location: loc.into(),
            card_type: card.into(),
            timestamp: ts.into(),
        }
    }

    #[test]
    fn low_risk_small_normal() {
        let r = score_transaction(&txn(10.0, "NYC", "credit", "2026-06-17T12:00:00Z"));
        assert_eq!(r.verdict, "Low Risk");
        assert!(r.score <= 30);
    }

    #[test]
    fn high_risk_large_unknown_prepaid_odd_hour() {
        let r = score_transaction(&txn(9000.0, "unknown", "prepaid", "2026-06-17T03:00:00Z"));
        assert_eq!(r.verdict, "High Risk");
        assert!(r.score >= 71);
        assert!(r.factors.contains(&"large_amount".to_string()));
        assert!(r.factors.contains(&"odd_hour".to_string()));
    }

    #[test]
    fn score_is_clamped() {
        let r = score_transaction(&txn(1_000_000.0, "unknown", "prepaid", "2026-06-17T02:00:00Z"));
        assert!(r.score <= 100);
    }

    #[test]
    fn boundary_medium() {
        let r = score_transaction(&txn(4000.0, "NYC", "credit", "2026-06-17T12:00:00Z"));
        assert_eq!(r.verdict, "Medium Risk");
    }
}
