class ServiceClient():

    #we have completed the service client, which is very similar to 
    #the oanda service client except for the code-label switch and contract math
    def __init__(self, brokerage_config=None):
        self.dwx_config = brokerage_config 
    
    def get_size_config(self, inst):
        if inst in self.dwx_config["fx"]:
            return self.dwx_config["order_min_contracts"]["fx"], \
                self.dwx_config["contract_size"]["fx"]
        elif inst in self.dwx_config["equities"]:
            return self.dwx_config["order_min_contracts"]["equities"], \
                self.dwx_config["contract_size"]["equities"]
        elif inst in self.dwx_config["commodities"]:
            return self.dwx_config["order_min_contracts"][inst], \
                self.dwx_config["contract_size"][inst]
        else:
            #let's limit our trading to fx equities and commodities for simplcity
            print("disallowed type")
            exit()

    def get_order_specs(self, inst, scaled_units, current_contracts):
        order_min_contracts, contract_size = self.get_size_config(inst)
        order_min_units = order_min_contracts * contract_size
        optimal_min_order = scaled_units / order_min_units
        rounded_min_order = round(optimal_min_order)
        return {
            "instrument": inst,
            "scaled_units": round(scaled_units, 5),
            "contract_size": contract_size,
            "order_min_contracts": order_min_contracts,
            "order_min_units": order_min_units,
            "optimal_contracts": round(optimal_min_order * order_min_contracts, 5),
            "rounded_contracts": round(rounded_min_order * order_min_contracts, 5),
            "current_contracts": current_contracts,
            "current_units": round(self.contracts_to_units(inst, current_contracts))
        }

    def label_to_code_nomenclature(self, label):
        #change EUR_USD back to EURUSD
        return label.replace("_", "")

    def code_to_label_nomenclature(self, code):
        if code in self.dwx_config["equities"]:
            return code
        if len(code) == 6:
            underscored = "{}_{}".format(code[0:3], code[3:])
            if underscored in self.dwx_config["fx"] or underscored in self.dwx_config["commodities"]:
                return "{}_{}".format(code[0:3], code[3:])
        return code

    def contracts_to_units(self, label, contracts):
        order_min_contracts, contract_size = self.get_size_config(label)
        return contracts * contract_size

    def units_to_contracts(self, label, units):
        order_min_contracts, contract_size = self.get_size_config(label)
        return units / contract_size
        
    def is_inertia_overriden(self, percent_change):
        return percent_change > 0.05