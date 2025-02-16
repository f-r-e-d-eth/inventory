import csv
from termcolor import colored

def format_case(text):
    return " ".join(word.capitalize() for word in text.split())

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
                recipes[current_product][component] = (amount, source)
    return recipes

def check_inventory(inventory, recipes):
    available_components = set()
    inventory_report = {}

    for product, components in recipes.items():
        product_report = []
        print(colored(f"Checking requirements for product: {product}", "cyan"))
        
        for component, (required_amount, source) in components.items():
            available_amount = inventory.get(component, 0)
            available_ratio = available_amount / required_amount if required_amount > 0 else 0
            
            # Assign colors based on availability percentage
            if available_ratio >= 1.0:
                color = "green"
                available_components.add(component)  # Mark as available
                display_value = f"{available_amount // required_amount}x"  # Factor when available
            elif available_ratio > 0:
                color = "yellow" if available_ratio >= 0.5 else "red"
                display_value = f"{available_ratio:.0%}"  # Show percentage when missing
            else:
                color = "red"
                display_value = "0%"  # Completely missing

            # Update source with better detail formatting
            if "//" in source:
                process, raw_components = source.split("//", 1)
                raw_components = raw_components.split("/")
                formatted_components = []
                for raw_component in raw_components:
                    raw_component_upper = raw_component.strip().upper()
                    component_required_amount = required_amount  # Default to required amount of the product
                    if raw_component_upper in inventory:
                        stock = inventory[raw_component_upper]
                        component_ratio = stock / component_required_amount if component_required_amount > 0 else 0
                        formatted_components.append(f"{raw_component.strip()}({component_ratio:.0%})")
                    else:
                        # Explicitly handle components not found or with zero stock
                        formatted_components.append(f"{raw_component.strip()}(0%)")

                source = f"{process}//{'/'.join(formatted_components)}"

            msg = f"{format_case(component)}: {display_value} (Needed: {required_amount}, Available: {available_amount}) (Source: {source})"

            print(colored(msg, color))
            product_report.append({"component": component, "needed": required_amount, "available": available_amount, "color": color, "source": source})

        inventory_report[product] = product_report
        print("")
    
    return inventory_report



def find_unneeded_inventory(inventory, recipes):
    needed_items = set()
    for components in recipes.values():
        needed_items.update(components.keys())
    unneeded_items = {item: amount for item, amount in inventory.items() if item not in needed_items}
    if unneeded_items:
        print(colored("\nUnneeded Inventory:", "red"))
        for item in sorted(unneeded_items):
            print(colored(f"{format_case(item)}: {unneeded_items[item]}", "white"))
    else:
        print(colored("\nNo unneeded inventory found.", "green"))

def list_needed_shortages(inventory, recipes):
    needed_shortages = {}
    for components in recipes.values():
        for item, (amount_needed, _) in components.items():
            needed_shortages[item] = needed_shortages.get(item, 0) + amount_needed
    for item, stored_amount in inventory.items():
        if item in needed_shortages:
            needed_shortages[item] -= stored_amount
    needed_shortages = {item: amount for item, amount in needed_shortages.items() if amount > 0}
    if needed_shortages:
        print(colored("\nNeeded Items (Shortages):", "blue"))
        for item in sorted(needed_shortages):
            total_needed = needed_shortages[item] + inventory.get(item, 0)
            available_ratio = inventory.get(item, 0) / total_needed if total_needed > 0 else 0
            if available_ratio >= 1.0:
                color = "green"
            elif available_ratio >= 0.5:
                color = "yellow"
            elif available_ratio >= 0.1:
                color = "white"
            else:
                color = "red"
            print(colored(f"{format_case(item)}: {needed_shortages[item]}", color))
    else:
        print(colored("\nNo shortages detected.", "green"))

def run_inventory_checks(processes):
    all_reports = {}
    for process in processes:
        print(colored(f"\n=== Processing {process['name']} ===\n", "magenta"))
        inventory_data = read_inventory(process["inventory"])
        recipes_data = read_recipes(process["recipe"])
        report = check_inventory(inventory_data, recipes_data)
        find_unneeded_inventory(inventory_data, recipes_data)
        list_needed_shortages(inventory_data, recipes_data)
        all_reports[process["name"]] = report
    return all_reports

def generate_html_report(all_reports):
    html_content = """
    <html>
    <head>
        <title>Inventory Report</title>
        <style>
            body { background-color: black; color: white; font-family: Arial, sans-serif; }
            h1, h2 { color: white; }
            table { width: 100%; border-collapse: collapse; margin: 2px 0; }
            th, td { border: 1px solid white; padding: 8px; text-align: left; }
            th { background-color: #444; }
            .green { color: lime; }
            .yellow { color: yellow; }
            .red { color: red; }
            .nested { width: 100%; border-collapse: collapse; border: none; }
            .nested td, .nested th { border: none; padding: 2px 5px; text-align: left; }
            .nested th { background-color: #444; padding: 4px 5px; } /* Light grey background for process names */
            .check { font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>Inventory Report</h1>
    """

    for process_name, reports in all_reports.items():
        html_content += f"<h2>{process_name}</h2><table>"
        html_content += "<tr><th>Component</th><th>Needed</th><th>Available</th><th>Status</th><th>Source</th></tr>"

        for product, details in reports.items():
            html_content += f"<tr><td colspan='5'><b>{product}</b></td></tr>"
            for item in details:
                color_class = item['color']
                if '//' in item['source']:
                    process_info, components = item['source'].split('//', 1)
                    components_list = components.split('/')
                    # Create nested table for source
                    source_html = f"<table class='nested'><tr><th>{process_info}</th></tr>"
                    for component in components_list:
                        comp_name, availability = component.rsplit('(', 1)
                        comp_avail = availability.rstrip(')%')
                        check_mark_color = "green" if int(comp_avail.replace('%', '')) >= 100 else "red"
                        check_mark = f"<span class='check {check_mark_color}'>{'✔' if check_mark_color == 'green' else '❌'}</span>"
                        source_html += f"<tr><td>{comp_name} ({availability} {check_mark}</td></tr>"
                    source_html += "</table>"
                else:
                    source_html = item['source']

                html_content += f"""
                <tr>
                    <td>{format_case(item['component'])}</td>
                    <td>{item['needed']}</td>
                    <td>{item['available']}</td>
                    <td class='{color_class}'>{'✔' if item['available'] >= item['needed'] else '❌'}</td>
                    <td>{source_html}</td>
                </tr>
                """

        html_content += "</table>"

    html_content += "</body></html>"

    with open("inventory_report.html", "w") as file:
        file.write(html_content)





processes = [
    {"name": "Stainless 00", "inventory": "/home/rs/Downloads/inventory_00.csv", "recipe": "recipe_stainless.txt"},
    {"name": "Alu 01", "inventory": "/home/rs/Downloads/inventory_01.csv", "recipe": "recipe_alu.txt"},
    {"name": "PowerMod 02", "inventory": "/home/rs/Downloads/inventory_02.csv", "recipe": "recipe_powerModul.txt"}
]

all_reports = run_inventory_checks(processes)
generate_html_report(all_reports)

print(all_reports)

