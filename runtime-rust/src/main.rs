fn banner() -> &'static str {
    "suiyu-rust-phase0"
}

fn main() {
    println!("{}", banner());
}

#[cfg(test)]
mod tests {
    #[test]
    fn banner_matches() {
        assert_eq!(super::banner(), "suiyu-rust-phase0");
    }
}
