//! Integration tests exercising the public library API.

use std::io::Write;

use logcount::{analyze_file, count_levels, Counts};

#[test]
fn counts_levels_in_text() {
    let text = "INFO ok\nWARN careful\nERROR bad\nWARNING also\n";
    assert_eq!(count_levels(text), Counts { info: 1, warn: 2, error: 1 });
}

#[test]
fn highest_severity_wins_per_line() {
    // A single line mentioning ERROR and WARN counts only as an error.
    let text = "ERROR and WARN on one line\nplain line\n";
    assert_eq!(count_levels(text), Counts { info: 0, warn: 0, error: 1 });
}

#[test]
fn missing_file_returns_error_not_panic() {
    let result = analyze_file("/no/such/file/at/all.log");
    assert!(result.is_err());
}

#[test]
fn reads_a_real_file() {
    let mut tmp = std::env::temp_dir();
    tmp.push("logcount_it_sample.log");
    let mut f = std::fs::File::create(&tmp).unwrap();
    writeln!(f, "INFO boot\nERROR crash").unwrap();

    let counts = analyze_file(&tmp).unwrap();
    assert_eq!(counts, Counts { info: 1, warn: 0, error: 1 });

    let _ = std::fs::remove_file(&tmp);
}
