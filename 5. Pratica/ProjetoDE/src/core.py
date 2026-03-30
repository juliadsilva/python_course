import yaml
import os

def load_configs():
	config_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'config.yml')
	with open(config_path, 'r', encoding='utf-8') as f:
		return yaml.safe_load(f)

configs = load_configs()
