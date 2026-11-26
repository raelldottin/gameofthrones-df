"""Compatibility entry point for the contract mutation suite."""
if __package__:
    from .mutation_runner import main
else:
    from mutation_runner import main

if __name__ == "__main__":
    raise SystemExit(main(["--suite", "contract"]))
