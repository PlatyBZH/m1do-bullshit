#!/usr/bin/env python3

import json

def load_json(file_path):
    '''
    load JSON data from a file
    '''
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print(f"File {file_path} not found.")
    except json.JSONDecodeError:
        print("Error decoding JSON.")
    except Exception as e:
        print(f"An error occurred: {e}")

def save_json(file_path, data):
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)  # Writing JSON data
        print(f"Data successfully written to {file_path}.")
    except Exception as e:
        print(f"An error occurred: {e}")

# Example usage
if __name__ == "__main__":
    file_path = 'data.json'
    json_data = load_json(file_path)
    print(json_data[0])
    filtered_data = [
        {
            'gender' : data['gender'],
            'baught_car_model' : data['baught_car_model'],
            'baught_car_year' : data['baught_car_year']
        }
        for data in json_data
    ]
    print(filtered_data[0])
    save_json("filtered_data.json", filtered_data)
