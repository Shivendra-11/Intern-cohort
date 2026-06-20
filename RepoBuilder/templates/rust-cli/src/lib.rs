//! Core log-counting logic, kept separate from `main.rs` so it is unit-testable.

use std::fs;
use std::io;
use std::path::Path;

/// Tally of log lines by severity level.
#[derive(Debug, Default, PartialEq, Eq)]
pub struct Counts {
    pub info: usize,
    pub warn: usize,
    pub error: usize,
}

/// Count INFO / WARN / ERROR lines in a block of text.
///
/// A line is counted once, by its highest severity: a line mentioning both
/// `ERROR` and `WARN` counts as an error. Matching is case-insensitive and
/// `WARN` also matches `WARNING`.
pub fn count_levels(text: &str) -> Counts {
    let mut counts = Counts::default();
    for line in text.lines() {
        let upper = line.to_uppercase();
        if upper.contains("ERROR") {
            counts.error += 1;
        } else if upper.contains("WARN") {
            counts.warn += 1;
        } else if upper.contains("INFO") {
            counts.info += 1;
        }
    }
    counts
}

/// Read a file and count its log levels.
///
/// Returns an `io::Error` (e.g. `NotFound`) if the file cannot be read, so the
/// caller can report it gracefully instead of panicking.
pub fn analyze_file<P: AsRef<Path>>(path: P) -> io::Result<Counts> {
    let text = fs::read_to_string(path)?;
    Ok(count_levels(&text))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn counts_each_level() {
        let text = "INFO starting\nWARN low disk\nERROR boom\nINFO done\n";
        let c = count_levels(text);
        assert_eq!(c, Counts { info: 2, warn: 1, error: 1 });
    }

    #[test]
    fn empty_input_is_all_zero() {
        assert_eq!(count_levels(""), Counts::default());
    }
}
