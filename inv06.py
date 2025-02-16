import csv
from termcolor import colored

def format_case(text):
    return " ".join(word.capitalize() for word in text.split())

def format_number(number):
    return f"{number:,}".replace(",", " ")


def read_inventory(file_path):
    inventory = {}
    with open(file_path, "r") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            inventory[row["product"].strip().upper()] = int(row["amount"].strip())
    return inventory

def read_recipes(file_path):
    recipes = {}
    with open(file_path, "r") as recipe_file:
        current_product = None
        for line in recipe_file:
            line = line.strip()
            if line.startswith("#product"):
                current_product = line.split()[1].strip().upper()
                recipes[current_product] = {}
            elif line and current_product:
                fields = line.split(",")
                component = fields[0].strip().upper()
                amount = int(fields[1].strip())
                source = fields[2].strip() if len(fields) > 2 else "Unknown"
                recipes[current_product][component] = {'amount': amount, 'source': source}
    return recipes

def check_inventory(inventory, recipes):
    inventory_report = {}
    for product, components in recipes.items():
        product_report = []
        for component, details in components.items():
            required_amount = details['amount']
            available_amount = inventory.get(component, 0)
            availability_percentage = (available_amount / required_amount * 100) if required_amount > 0 else 0
            
            # Correcting the processing of source information to accurately reflect individual component percentages
            source_info = details['source']
            if "//" in source_info:
                process, raw_components = source_info.split("//", 1)
                formatted_components = []
                for raw_component in raw_components.split("/"):
                    raw_comp_name = raw_component.strip().upper()
                    if raw_comp_name in recipes[product]:  # Ensure we are referencing the right component amount
                        raw_required_amount = recipes[product][raw_comp_name]['amount']
                        raw_available_amount = inventory.get(raw_comp_name, 0)
                        raw_percentage = (raw_available_amount / raw_required_amount * 100) if raw_required_amount > 0 else 0
                        color_class = 'green' if raw_percentage > 100 else 'normal'
                        formatted_components.append(f"{raw_comp_name}({raw_percentage:.1f}%)")
                    else:
                        formatted_components.append(f"{raw_comp_name}(0%)")
                formatted_source = f"{process}//{'/'.join(formatted_components)}"
            else:
                formatted_source = source_info

            product_report.append({
                "component": component,
                "needed": required_amount,
                "available": available_amount,
                "availability_percent": availability_percentage,
                "source": formatted_source
            })

        inventory_report[product] = product_report

    return inventory_report

# Note: The generate_html_report function should now reference the correct coloring and percentage calculation from check_inventory.


def generate_html_report(all_reports):
    html_content = """
    <html>
    <head>
        <title>Inventory Report</title>
        <style>
            body { display: flex; background-color: black; color: white; font-family: Arial, sans-serif; margin: 0; }
            #sidebar { width: 200px; background-color: #333; color: white; padding: 20px; position: fixed; height: 100vh; overflow: auto; }
            #main { flex-grow: 1; margin-left: 220px; padding: 20px; }
            table { width: 100%; border-collapse: collapse; }
            th, td { border: 1px solid white; padding: 8px; }
            th { background-color: #444; }
            .green { color: limegreen; }
            .normal { color: white; }
            .process { background-color: #444; color: white; font-weight: bold; }
            .quantities { font-size: 0.8em; text-align: right; line-height: 1.2; }
            a { color: white; text-decoration: none; }
            a:hover { text-decoration: underline; }
            .center { text-align: center; } /* Class to center text */
            ul { padding-left: 0; list-style: none; }
            ul li { padding: 5px 0; }
            ul li ul { padding-left: 20px; }
        </style>
    </head>
    <body>
        <div id='sidebar'>
            <h3>Navigation</h3>
            <ul>"""
    # Generate sidebar links with subcategories for each product under a process
    for process_name, details in all_reports.items():
        html_content += f"<li><a href='#{process_name}'>{process_name}</a>"
        html_content += "<ul>"
        for product, product_details in details.items():
            product_id = f"{process_name}_{product}".replace(" ", "_")  # Create a unique ID by combining process and product names
            # Determine if all components are sufficiently available
            all_sufficient = all(item['availability_percent'] > 100 for item in product_details)
            link_color_class = 'green' if all_sufficient else 'normal'
            html_content += f"<li><a href='#{product_id}' class='{link_color_class}'>{format_case(product)}</a></li>"
        html_content += "</ul></li>"

    html_content += "</ul></div><div id='main'><h1>Inventory Report</h1>"
    
    # Generate main content
    for process_name, details in all_reports.items():
        html_content += f"<h2 id='{process_name}'>{process_name}</h2>"
        for product, product_details in details.items():
            product_id = f"{process_name}_{product}".replace(" ", "_")
            html_content += f"<h3 id='{product_id}'>{format_case(product)}</h3>"
            html_content += "<table><tr><th>Component</th><th>(Needed / Available)</th><th>Availability %</th><th>Source</th></tr>"
            for item in product_details:
                needed_formatted = format_number(item['needed'])
                available_formatted = format_number(item['available'])
                percent_value = item['availability_percent']
                availability_class = 'green' if percent_value > 100 else 'normal'
                availability_formatted = f"{percent_value:.0f}%"
                html_content += f"<tr><td>{format_case(item['component'])}</td><td class='quantities'>{needed_formatted}<br>{available_formatted}</td><td class='{availability_class} center'>{availability_formatted}</td><td>"

                if "//" in item['source']:
                    process, components = item['source'].split("//", 1)
                    html_content += f"<div class='process'>{format_case(process)}</div>"
                    components_list = components.split("/")
                    for component in components_list:
                        if component:
                            comp_name, comp_percent = component.rsplit('(', 1)
                            comp_percent_value = int(float(comp_percent.rstrip('%)')))
                            color_class = 'green' if comp_percent_value > 100 else 'normal'
                            comp_name = format_case(comp_name.strip())
                            html_content += f"<span class='{color_class}'>{comp_name} ({comp_percent_value}%)</span><br>"
                else:
                    html_content += format_case(item['source'])
                    
                html_content += "</td></tr>"
            html_content += "</table>"

    html_content += "</div></body></html>"

    with open("inventory_report.html", "w") as file:
        file.write(html_content)

def run_inventory_checks(processes):
    all_reports = {}
    for process in processes:
        inventory = read_inventory(process["inventory"])
        recipes = read_recipes(process["recipe"])
        report = check_inventory(inventory, recipes)
        all_reports[process["name"]] = report
    return all_reports

# Example usage
processes = [
    {"name": "Stainless 00", "inventory": "/home/rs/Downloads/inventory_00.csv", "recipe": "recipe_stainless.txt"},
    {"name": "Alu 01", "inventory": "/home/rs/Downloads/inventory_01.csv", "recipe": "recipe_alu.txt"},
    {"name": "PowerMod 02", "inventory": "/home/rs/Downloads/inventory_02.csv", "recipe": "recipe_powerModul.txt"}
]

all_reports = run_inventory_checks(processes)
generate_html_report(all_reports)

