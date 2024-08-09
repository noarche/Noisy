import os
import re

def process_domains(file_path):
    # Read the content of the file
    with open(file_path, 'r') as file:
        domains = file.readlines()

    # Prepare the list of filtered domains
    filtered_domains = []
    for domain in domains:
        # Remove leading/trailing whitespace and ensure only one domain per line
        domain = domain.strip()
        # Check if the domain contains a number or more than one '.'
        if not re.search(r'\d', domain) and domain.count('.') == 1:
            filtered_domains.append(domain)
    
    # Create the new file name
    dir_name, base_name = os.path.split(file_path)
    new_file_name = os.path.join(dir_name, base_name.replace('.txt', '_edit.txt'))

    # Write the filtered domains to the new file
    with open(new_file_name, 'w') as new_file:
        for domain in filtered_domains:
            new_file.write(domain + '\n')

    print(f"Filtered domains have been saved to: {new_file_name}")

def main():
    # Prompt the user for the source file path
    source_file = input("Please enter the path to the source file: ")
    if os.path.isfile(source_file):
        process_domains(source_file)
    else:
        print("The file does not exist. Please check the path and try again.")

if __name__ == "__main__":
    main()
