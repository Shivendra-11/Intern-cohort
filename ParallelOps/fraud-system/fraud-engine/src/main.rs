use std::io::{self, Read};

use fraud_engine::{score_transaction, Txn};

fn main() {
    let mut input = String::new();
    if io::stdin().read_to_string(&mut input).is_err() {
        eprintln!("failed to read stdin");
        std::process::exit(1);
    }
    let txn: Txn = match serde_json::from_str(&input) {
        Ok(t) => t,
        Err(e) => {
            eprintln!("invalid txn json: {e}");
            std::process::exit(2);
        }
    };
    let result = score_transaction(&txn);
    println!("{}", serde_json::to_string(&result).unwrap());
}
