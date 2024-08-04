import json

def parse_domains_to_json(input_file, output_file):
    with open(input_file, 'r') as file:
        domains = file.readlines()
        
    root_urls = ["https://" + domain.strip() for domain in domains]
    config = {
        "root_urls": root_urls,
        "blacklisted_urls": [],
        "max_depth": 5,
        "timeout": 9999999999,
        "min_sleep": 30,
        "max_sleep": 120
    }

    with open(output_file, 'w') as json_file:
        json.dump(config, json_file, indent=4)

if __name__ == "__main__":
    # Input file containing the list of domains
    input_file = "list.txt"
    
    # Output JSON file
    output_file = "config.json"

    parse_domains_to_json(input_file, output_file)
    print(f"Configuration saved to {output_file}")
