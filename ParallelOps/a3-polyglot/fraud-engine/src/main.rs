//! CLI entry point for the fraud engine.
//!
//! Reads a single transaction as JSON on **stdin** and writes the scoring
//! result as JSON on **stdout**:
//!
//!   echo '{"amount":4200.5,"location":"NYC","card_type":"credit","timestamp":"2026-06-17T03:00:00Z"}' \
//!     | fraud-engine
//!   => {"score":57,"verdict":"Medium Risk","factors":[...]}
//!
//! Exits non-zero (without panicking) if stdin is not valid JSON, so the Node
//! worker can surface the error instead of crashing.

use std::io::{self, Read};
use std::process::ExitCode;

use fraud_engine::{score_transaction, Txn};

fn main() -> ExitCode {
    let mut buf = String::new();
    if let Err(err) = io::stdin().read_to_string(&mut buf) {
        eprintln!("error: could not read stdin: {}", err);
        return ExitCode::FAILURE;
    }

    let txn: Txn = match serde_json::from_str(&buf) {
        Ok(t) => t,
        Err(err) => {
            eprintln!("error: invalid transaction JSON: {}", err);
            return ExitCode::FAILURE;
        }
    };

    let scored = score_transaction(&txn);
    match serde_json::to_string(&scored) {
        Ok(json) => {
            println!("{}", json);
            ExitCode::SUCCESS
        }
        Err(err) => {
            eprintln!("error: could not serialize result: {}", err);
            ExitCode::FAILURE
        }
    }
}
