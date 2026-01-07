#!/usr/bin/env python3
"""
Setup script for Ollama Gateway
Initializes the database with sample data for testing
"""

import secrets

from database import Database


def setup_database():
    """Initialize database with sample data"""
    print("Setting up Ollama Gateway...")
    print()
    
    # Initialize database
    db = Database(db_path="gateway_data_volume/llm_gateway.db")
    print("Database initialized")
    
    # Add sample models with pricing
    print("\nAdding sample models...")
        
    models = [
            ("qwen3:4b-q4_K_M",0.01,0.02),
            ("qwen3:1.7b",0.01,0.02),
            ("qwen3:0.6b",0.01,0.02),
            ("qwen3:8b",0.01,0.02),
            ("deepseek-r1:7b",0.01,0.02),
            ("deepseek-r1:14b",0.01,0.02),
            ("deepseek-r1:8b",0.01,0.02),
            ("deepseek-r1:1.5b",0.01,0.02),
            ("llama3.2:latest",0.01,0.02),
            ("gpt-oss:20b",0.1,0.2),

    ]
    
    for model_name, input_cost, output_cost in models:
        db.add_model(model_name, input_cost, output_cost)
        print(f"Added {model_name} (input: ${input_cost}/1K, output: ${output_cost}/1K)")
    
    # Create sample users
    print("\nCreating sample users...")
    sample_users = ["Vaibhav", "Nayan", "Priti"]
    user_ids = {}
    
    for username in sample_users:
        user_id = db.create_user(username)
        if user_id:
            user_ids[username] = user_id
            print(f"Created user: {username} (ID: {user_id})")
    
    # Generate sample API keys
    print("\nGenerating sample API keys...")
    
    if "Vaibhav" in user_ids:
        # Vaibhav: Full access, $100 limit
        api_key = f"llmgw-{secrets.token_urlsafe(32)}"
        db.create_api_key(
            user_id=user_ids["Vaibhav"],
            api_key=api_key,
            allowed_models=["*"],  # All models
            cost_limit=100.0
        )
        print(f"Vaibhav's API key (all models, $100 limit):")
        print(f"    {api_key}")
    
    if "Nayan" in user_ids:
        # Nayan: Limited access, $50 limit
        api_key = f"llmgw-{secrets.token_urlsafe(32)}"
        db.create_api_key(
            user_id=user_ids["Nayan"],
            api_key=api_key,
            allowed_models=["qwen3:0.6b", "qwen3:1.7b", "qwen3:4b-q4_K_M", "qwen3:8b"],
            cost_limit=50.0
        )
        print(f"Nayan's API key (qwen3:*, $500 limit):")
        print(f"    {api_key}")
    
    if "Priti" in user_ids:
        # Priti: Code models only, unlimited
        api_key = f"llmgw-{secrets.token_urlsafe(32)}"
        db.create_api_key(
            user_id=user_ids["Priti"],
            api_key=api_key,
            allowed_models=["qwen3:0.6b", "deepseek-r1:1.5b"],
            cost_limit=0.0  # Unlimited
        )
        print(f"Priti's API key (code models, unlimited):")
        print(f"    {api_key}")
    
    print("\n" + "="*60)
    print("Setup completed successfully!")
    print("="*60)
    print("\nNext steps:")
    print("1. Start the gateway: python gateway_api.py")
    print("2. Start the dashboard: streamlit run dashboard.py")
    print("3. Access the dashboard at: http://localhost:8501")
    print("4. Use the API keys above to test the gateway")
    print("\n" + "="*60)


def reset_database():
    """Reset database (WARNING: This deletes all data!)"""
    import os
    
    print("WARNING: This will delete all existing data!")
    response = input("Are you sure you want to reset the database? (yes/no): ")
    
    if response.lower() == 'yes':
        if os.path.exists("gateway_data_volume/llm_gateway.db"):
            os.remove("gateway_data_volume/llm_gateway.db")
            print("Database reset successfully")
            setup_database()
        else:
            print("No existing database found")
            setup_database()
    else:
        print("Reset cancelled")


def add_demo_usage():
    """Add some demo usage data for testing analytics"""
    import random
    from datetime import datetime, timedelta
    
    print("\nAdding demo usage data...")
    db = Database()
    
    # Get users and API keys
    users = db.get_all_users()
    if not users:
        print("No users found. Run setup first.")
        return
    
    models = ["llama2", "mistral", "codellama"]
    endpoints = ["/api/chat", "/api/generate"]
    
    # Generate usage for the last 7 days
    for user in users:
        api_keys = db.get_user_api_keys(user['id'])
        if not api_keys:
            continue
        
        api_key = api_keys[0]  # Use first API key
        
        # Generate 20-50 requests per user
        num_requests = random.randint(20, 50)
        
        for _ in range(num_requests):
            # Random model and endpoint
            model = random.choice(models)
            endpoint = random.choice(endpoints)
            
            # Random token counts
            input_tokens = random.randint(50, 500)
            output_tokens = random.randint(100, 1000)
            
            # Calculate cost
            pricing = db.get_model_pricing(model)
            if pricing:
                cost = (input_tokens / 1000 * pricing['input_cost_per_1k'] +
                       output_tokens / 1000 * pricing['output_cost_per_1k'])
            else:
                cost = 0.0
            
            # Random response time
            response_time = random.uniform(0.5, 5.0)
            
            # Random status (95% success)
            status = "success" if random.random() < 0.95 else "error"
            
            # Log usage
            db.log_usage(
                api_key_id=api_key['id'],
                user_id=user['id'],
                model_name=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                response_time=response_time,
                cost=cost,
                endpoint=endpoint,
                status=status
            )
            
            # Update API key cost
            if status == "success":
                db.update_api_key_cost(api_key['id'], cost)
    
    print(f"Added demo usage data for {len(users)} users")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "reset":
            reset_database()
        elif sys.argv[1] == "demo":
            add_demo_usage()
        else:
            print("Usage:")
            print("  python setup.py        - Initial setup")
            print("  python setup.py reset  - Reset database")
            print("  python setup.py demo   - Add demo usage data")
    else:
        setup_database()
