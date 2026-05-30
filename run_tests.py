import sys
import pytest

sys.path.insert(0, 'src')
sys.exit(pytest.main(['-v', '--tb=short']))
