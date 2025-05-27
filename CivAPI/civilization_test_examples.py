# test_examples.py
"""
Example usage and test cases for the Civilization Database API
"""
import requests
import json


class CivilizationAPIClient:
    """Simple client for testing the Civilization API"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def create_civilization(self, civilization_data):
        """Create a new civilization"""
        response = self.session.post(
            f"{self.base_url}/civilizations/",
            json=civilization_data
        )
        return response.json() if response.status_code == 200 else response.text
    
    def get_civilization(self, civilization_id):
        """Get a civilization by ID"""
        response = self.session.get(f"{self.base_url}/civilizations/{civilization_id}")
        return response.json() if response.status_code == 200 else response.text
    
    def list_civilizations(self, **filters):
        """List civilizations with optional filters"""
        response = self.session.get(
            f"{self.base_url}/civilizations/",
            params=filters
        )
        return response.json() if response.status_code == 200 else response.text
    
    def search_civilizations(self, query):
        """Search civilizations"""
        response = self.session.get(
            f"{self.base_url}/civilizations/search",
            params={"q": query}
        )
        return response.json() if response.status_code == 200 else response.text
    
    def get_statistics(self):
        """Get civilization statistics"""
        response = self.session.get(f"{self.base_url}/civilizations/statistics")
        return response.json() if response.status_code == 200 else response.text


# Example civilization data
medieval_kingdom = {
    "name": "Kingdom of Aethermoor",
    "description": "A medieval kingdom known for its fertile plains and skilled craftsmen",
    "tags": ["medieval", "agricultural", "monarchy"],
    "created_by": "test_user",
    "settlement_pattern": "settled",
    "primary_terrain": "plains",
    "population_density": "medium",
    "architecture_style": "stone",
    "government_type": "monarchy",
    "leadership_selection": "hereditary",
    "centralization_level": "highly_centralized",
    "legal_system": "common_law",
    "primary_economy": "agricultural",
    "trade_orientation": "regional_trade",
    "currency_type": "metal_coins",
    "property_rights": "private",
    "social_stratification": "class_based",
    "gender_roles": "patriarchal",
    "family_structure": "extended",
    "age_hierarchy": "elder_led",
    "primary_religion": "monotheistic",
    "religious_influence": "strong_influence",
    "art_focus": "architecture",
    "cultural_values": "honor_based",
    "education_system": "apprenticeship",
    "literacy_rate": "low",
    "knowledge_basis": "traditional_cultural",
    "technology_level": "iron_age",
    "military_structure": "professional_army",
    "warfare_approach": "defensive_only",
    "primary_weapons": "melee",
    "language_complexity": "moderate",
    "writing_system": "alphabetic",
    "communication_methods": "written",
    "resource_use": "sustainable",
    "agriculture_type": "intensive",
    "energy_sources": "human_animal",
    "population_size": "medium",
    "life_expectancy": "short",
    "technological_adoption": "conservative",
    "external_relations": "cautious",
    "change_rate": "slow_changing",
    "exact_population": 150000,
    "exact_life_expectancy": 45.5,
    "territory_size_km2": 25000.0
}

space_federation = {
    "name": "Stellar Confederation",
    "description": "An advanced space-faring civilization spanning multiple star systems",
    "tags": ["space-age", "democratic", "post-scarcity"],
    "created_by": "test_user",
    "settlement_pattern": "urban",
    "primary_terrain": "mixed",
    "population_density": "high",
    "architecture_style": "metal",
    "government_type": "democracy",
    "leadership_selection": "elected",
    "centralization_level": "federal",
    "legal_system": "civil_law",
    "primary_economy": "service",
    "trade_orientation": "international_trade",
    "currency_type": "digital",
    "property_rights": "mixed",
    "social_stratification": "meritocratic",
    "gender_roles": "egalitarian",
    "family_structure": "nuclear",
    "age_hierarchy": "age_egalitarian",
    "primary_religion": "atheistic",
    "religious_influence": "secular",
    "art_focus": "mixed",
    "cultural_values": "achievement_oriented",
    "education_system": "formal_schools",
    "literacy_rate": "universal",
    "knowledge_basis": "empirical_scientific",
    "technology_level": "post_scarcity",
    "military_structure": "professional_army",
    "warfare_approach": "diplomatic",
    "primary_weapons": "advanced_technology",
    "language_complexity": "complex",
    "writing_system": "alphabetic",
    "communication_methods": "digital",
    "resource_use": "sustainable",
    "agriculture_type": "industrial",
    "energy_sources": "renewable",
    "population_size": "massive",
    "life_expectancy": "very_long",
    "technological_adoption": "technophilic",
    "external_relations": "cosmopolitan",
    "change_rate": "rapid_change",
    "exact_population": 2500000000,
    "exact_life_expectancy": 150.0,
    "territory_size_km2": 1000000000.0
}

nomadic_tribes = {
    "name": "Desert Wanderers",
    "description": "Nomadic tribes that traverse the great desert following ancient migration routes",
    "tags": ["nomadic", "desert", "tribal"],
    "created_by": "test_user",
    "settlement_pattern": "nomadic",
    "primary_terrain": "desert",
    "population_density": "sparse",
    "architecture_style": "temporary",
    "government_type": "tribal_council",
    "leadership_selection": "elected",
    "centralization_level": "decentralized",
    "legal_system": "customary_law",
    "primary_economy": "pastoral",
    "trade_orientation": "local_trade_only",
    "currency_type": "barter",
    "property_rights": "communal",
    "social_stratification": "egalitarian",
    "gender_roles": "complementary",
    "family_structure": "clan_based",
    "age_hierarchy": "elder_led",
    "primary_religion": "animistic",
    "religious_influence": "moderate_influence",
    "art_focus": "music",
    "cultural_values": "harmony_focused",
    "education_system": "oral_tradition",
    "literacy_rate": "none",
    "knowledge_basis": "traditional_cultural",
    "technology_level": "bronze_age",
    "military_structure": "militia",
    "warfare_approach": "raiding_culture",
    "primary_weapons": "ranged_primitive",
    "language_complexity": "simple",
    "writing_system": "none",
    "communication_methods": "oral_only",
    "resource_use": "sustainable",
    "agriculture_type": "none",
    "energy_sources": "human_animal",
    "population_size": "small",
    "life_expectancy": "short",
    "technological_adoption": "conservative",
    "external_relations": "isolationist",
    "change_rate": "static",
    "exact_population": 8000,
    "exact_life_expectancy": 35.0,
    "territory_size_km2": 50000.0
}


def run_examples():
    """Run example API calls"""
    client = CivilizationAPIClient()
    
    print("=== Civilization Database API Examples ===\n")
    
    # Test API health
    try:
        response = client.session.get(f"{client.base_url}/health")
        print(f"API Health: {response.json()}\n")
    except:
        print("API is not running. Please start the server first.\n")
        return
    
    # Create civilizations
    print("1. Creating civilizations...")
    
    medieval_result = client.create_civilization(medieval_kingdom)
    print(f"Created Medieval Kingdom: {medieval_result}")
    
    space_result = client.create_civilization(space_federation)
    print(f"Created Space Federation: {space_result}")
    
    nomadic_result = client.create_civilization(nomadic_tribes)
    print(f"Created Nomadic Tribes: {nomadic_result}\n")
    
    # List all civilizations
    print("2. Listing all civilizations...")
    all_civs = client.list_civilizations()
    print(f"Total civilizations: {all_civs.get('total', 0)}")
    if 'civilizations' in all_civs:
        for civ in all_civs['civilizations']:
            print(f"  - {civ['metadata']['name']} ({civ['metadata']['technology_level']})")
    print()
    
    # Filter civilizations
    print("3. Filtering civilizations by government type...")
    democracies = client.list_civilizations(government_type="democracy")
    print(f"Democracies found: {democracies.get('total', 0)}")
    
    monarchies = client.list_civilizations(government_type="monarchy")
    print(f"Monarchies found: {monarchies.get('total', 0)}")
    
    tribal = client.list_civilizations(government_type="tribal_council")
    print(f"Tribal councils found: {tribal.get('total', 0)}\n")
    
    # Search civilizations
    print("4. Searching civilizations...")
    search_results = client.search_civilizations("desert")
    print(f"Search for 'desert': {search_results.get('total', 0)} results")
    
    search_results = client.search_civilizations("space")
    print(f"Search for 'space': {search_results.get('total', 0)} results\n")
    
    # Get statistics
    print("5. Getting statistics...")
    stats = client.get_statistics()
    print(f"Statistics: {json.dumps(stats, indent=2)}\n")
    
    # Get specific civilization
    if 'civilizations' in all_civs and all_civs['civilizations']:
        civ_id = all_civs['civilizations'][0]['id']
        print(f"6. Getting specific civilization (ID: {civ_id})...")
        specific_civ = client.get_civilization(civ_id)
        if 'metadata' in specific_civ:
            print(f"Retrieved: {specific_civ['metadata']['name']}")
            print(f"Population: {specific_civ['metadata'].get('exact_population', 'Unknown')}")
            print(f"Technology: {specific_civ['metadata']['technology_level']}")
    
    print("\n=== Examples completed ===")


if __name__ == "__main__":
    run_examples()