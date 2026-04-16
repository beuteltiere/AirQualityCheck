import csv

def fahrenheit_to_celsius(fahrenheit):
    return (fahrenheit - 32) * 5 / 9

def convert_csv(input_file, output_file):
    with open(input_file, 'r', newline='') as infile, open(output_file, 'w', newline='') as outfile:
        reader = csv.reader(infile)
        writer = csv.writer(outfile)
        
        # Read and write header
        header = next(reader)
        writer.writerow(header)
        
        for row in reader:
            room, time, temp_str = row
            temp_f = float(temp_str)
            temp_c = fahrenheit_to_celsius(temp_f)
            # Round to 2 decimal places to match original format
            temp_c_rounded = round(temp_c, 2)
            writer.writerow([room, time, temp_c_rounded])

if __name__ == "__main__":
    input_file = "TestTempInFahrenheit.csv"
    output_file = "TestTempInCelsius.csv"
    convert_csv(input_file, output_file)
    print("Conversion complete. Output saved to TestTempInCelsius.csv")