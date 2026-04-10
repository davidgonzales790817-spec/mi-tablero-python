def extract_classifier_codes(data):
    # Example implementation to extract classifier codes
    return [row['classifier_code'] for row in data if 'classifier_code' in row]


def extract_classifier_descriptions(data):
    # Example implementation to extract classifier descriptions
    return [row['description'] for row in data if 'description' in row]


def detect_classifier_columns(data):
    # Example implementation to detect relevant classifier columns
    return [key for key in data[0].keys() if 'classifier' in key]


def display_classifier_info(data):
    codes = extract_classifier_codes(data)
    descriptions = extract_classifier_descriptions(data)
    classifier_columns = detect_classifier_columns(data)

    # Logic to display these using tables and charts
    for code, description in zip(codes, descriptions):
        print(f'{code} - {description}')  # Replace with actual display logic


# Integrating these functions in the drilldown detail

# Example usage:
if __name__ == '__main__':
    data = [{ 'classifier_code': '2.1.4.1.1.1', 'description': 'COMPENSACION POR TIEMPO DE SERVICIOS' }]
    display_classifier_info(data)
