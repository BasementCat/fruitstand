import sys, os
sys.stdout = sys.stderr
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(sys.path[0])
from fruitstand import app as application