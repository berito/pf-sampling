"""pfexp — particle-filter sampling experiments built on upstream code fetched into vendor/."""
import sys

# Never write __pycache__ folders, whichever Python imports this package (the container, a local Python, or
# an editor's test discovery): importing upstream code must leave vendor/ untouched.
sys.dont_write_bytecode = True
