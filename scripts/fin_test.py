from .top_day import run as collect_top_day
from .new import run as collect_new
from .hot import run as collect_hot

from .c_top import run as collect_c_top
from .c_new import run as collect_c_new 
from .c_hot import run as collect_c_hot

def run_all():
    collect_top_day()
    collect_new()
    collect_hot()
    collect_c_top()
    collect_c_new()
    collect_c_hot()

if __name__ == "__main__":
    run_all()