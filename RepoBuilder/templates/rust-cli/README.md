# logcount (Rust CLI)

A small command-line tool that counts `INFO` / `WARN` / `ERROR` lines in a log file.

- Each line is counted once by its highest severity (a line with both `ERROR`
  and `WARN` counts as an error).
- Matching is case-insensitive; `WARN` also matches `WARNING`.
- A missing/unreadable file prints a friendly message to stderr and exits with a
  non-zero status (it does not panic).

## Build

```bash
cargo build
```

## Run

```bash
cargo run -- path/to/app.log
# or, after building:
./target/debug/logcount path/to/app.log
```

Example output:

```
INFO:  12
WARN:  3
ERROR: 1
```

Missing file:

```bash
$ cargo run -- nope.log
error: could not read 'nope.log': No such file or directory (os error 2)
$ echo $?
1
```

## Test

```bash
cargo test
```

Tests live inline in `src/lib.rs` (unit) and in `tests/integration.rs` (integration).
