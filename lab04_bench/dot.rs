use std::env;
use std::fs;
use std::hint::black_box;
use std::io::{self, BufRead, Write};

fn read_vector(path: &str, n: usize) -> Result<Vec<f64>, String> {
    let bytes = fs::read(path).map_err(|error| error.to_string())?;
    if n.checked_mul(8) != Some(bytes.len()) {
        return Err("invalid binary vector".into());
    }
    Ok(bytes.chunks_exact(8)
        .map(|chunk| f64::from_le_bytes(chunk.try_into().unwrap()))
        .collect())
}

fn dot(a: &[f64], b: &[f64]) -> Result<f64, String> {
    if a.len() != b.len() {
        return Err("length mismatch".into());
    }
    let mut total = 0.0;
    for (&x, &y) in a.iter().zip(b.iter()) {
        total += x * y;
    }
    Ok(total)
}

fn worker() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().skip(1).collect();
    let [n, m, path_a, path_b] = args.as_slice() else {
        return Err("invalid arguments".into());
    };
    let (n, m) = (n.parse::<usize>()?, m.parse::<usize>()?);
    if n != m {
        return Err("length mismatch".into());
    }
    let (a, b) = (read_vector(path_a, n)?, read_vector(path_b, m)?);
    let mut out = io::stdout().lock();
    let mode = if cfg!(debug_assertions) { "debug" } else { "release" };
    writeln!(out, "READY {mode}")?;
    out.flush()?;
    let mut checksum = 0.0;
    for line in io::stdin().lock().lines() {
        let line = line?;
        let command: Vec<_> = line.split_whitespace().collect();
        match command.as_slice() {
            ["go", reps] => {
                let reps: usize = reps.parse()?;
                if reps == 0 {
                    return Err("repetitions must be positive".into());
                }
                checksum = 0.0;
                for _ in 0..reps {
                    checksum += black_box(dot(black_box(&a), black_box(&b))?);
                }
                writeln!(out, "DONE")?;
            }
            ["sum"] => writeln!(out, "{checksum:.17e}")?,
            ["ping"] => writeln!(out, "DONE")?,
            _ => return Err("invalid command".into()),
        }
        out.flush()?;
    }
    Ok(())
}

fn main() {
    if let Err(error) = worker() {
        eprintln!("{error}");
        std::process::exit(2);
    }
}
