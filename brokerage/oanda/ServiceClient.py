#dependency not on the oandav20 api, but handles order logic math
class ServiceClient():

    def __int__(self, brokerage_config=None):
        self.brokerage_config=brokerage_config

    def get_size_config(self, inst):
        order_min_contracts = 1
        contract_size = 1
        return order_min_contracts, contract_size

    def get_order_specs(self, inst, scaled_units, current_contracts):
        #let this be the internal  order config/specs
        #so this is the ORDER DICT passed between different components
        #regardless of the brokerage, this `internal specs` need to be specified
        
        #smallest contracts allowed in an order, size of a contract
        order_min_contracts, contract_size = self.get_size_config(inst)
        
        #smallest units allowed in an order
        order_min_units = order_min_contracts * contract_size
        
        #number of minimally sized orders of position we want to have in `units`
        optimal_min_order = scaled_units / order_min_units
        rounded_min_order = round(optimal_min_order)
        
        return {
            "instrument": inst,
            "scaled_units": scaled_units,
            "contract_size": contract_size,
            "order_min_contracts": order_min_contracts,
            "order_min_units": order_min_units,
            "optimal_contracts": optimal_min_order * order_min_contracts,
            "rounded_contracts": rounded_min_order * order_min_contracts,
            "current_contracts": current_contracts,
            "current_units": self.contracts_to_units(inst, current_contracts)
        }

    def label_to_code_nomenclature(self, label):
        #let label be the internal ticker symbol
        #and the code be the brokerage symbol
        #so for instance, the label EUR_USD can refer to
        #EUR/USD || EUR USD || EUR.USD || ...
        return label

    def code_to_label_nomenclature(self, code):
        return code

    def contracts_to_units(self, label, contracts):
        order_min_contracts, contract_size = self.get_size_config(label)
        return contracts * contract_size

    def units_to_contracts(self, label, units):
        order_min_contracts, contract_size = self.get_size_config(label)
        return units / contract_size
        
    def is_inertia_overriden(self, percent_change):
        return percent_change > 0.05