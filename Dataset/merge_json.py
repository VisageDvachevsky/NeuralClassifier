import json
import os

def combine_json_files(json_files, output_file):
    combined_data = {}

    for json_file in json_files:
        with open(json_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
            for key, value in data.items():
                if key in combined_data:
                    if isinstance(value, list):
                        combined_data[key] = list(set(combined_data[key] + value))
                    elif isinstance(value, dict):
                        for subkey, subvalue in value.items():
                            if subkey in combined_data[key]:
                                combined_data[key][subkey] = list(set(combined_data[key][subkey] + subvalue))
                            else:
                                combined_data[key][subkey] = subvalue
                else:
                    combined_data[key] = value

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(combined_data, file, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    json_files = []
    for i in range(3):
        json_file = input(f"Enter the name of JSON file {i+1}: ")
        json_files.append(json_file)

    output_file = os.path.join("Resources", "_dataset.assets", input("Enter the name of the final JSON file: "))

    combine_json_files(json_files, output_file)
    print(f"Combined JSON saved to {output_file}")
