//! CLI entry point: count INFO/WARN/ERROR lines in a log file.

use std::process::ExitCode;

use clap::Parser;
use logcount::analyze_file;

#[derive(Parser)]
#[command(name = "logcount", about = "Count INFO/WARN/ERROR lines in a log file")]
struct Cli {
    /// Path to the log file to analyze
    file: String,
}

fn main() -> ExitCode {
    let cli = Cli::parse();
    match analyze_file(&cli.file) {
        Ok(counts) => {
            println!("INFO:  {}", counts.info);
            println!("WARN:  {}", counts.warn);
            println!("ERROR: {}", counts.error);
            ExitCode::SUCCESS
        }
        Err(err) => {
            eprintln!("error: could not read '{}': {}", cli.file, err);
            ExitCode::FAILURE
        }
    }
}
