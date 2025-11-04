#!/usr/bin/env python3
"""
Setup AgentCore Memory for Medical Assistant
"""

import boto3
from bedrock_agentcore.memory import MemoryClient
from bedrock_agentcore.memory.constants import StrategyType

def setup_medical_memory():
    """Create AgentCore memory for medical assistant"""
    
    # Initialize clients
    memory_client = MemoryClient()
    ssm = boto3.client('ssm')
    
    # Memory configuration for medical assistant
    memory_name = "MedicalAssistantMemory"
    ssm_param = "/app/medicalassistant/agentcore/memory_id"
    
    # Define memory strategies for medical conversations
    strategies = [
        {
            StrategyType.SEMANTIC.value: {
                "name": "medical_facts_extractor",
                "description": "Extracts and stores medical facts and patient information",
                "namespaces": ["medical/patient/{actorId}/facts"],
            },
        },
        {
            StrategyType.SUMMARY.value: {
                "name": "consultation_summary",
                "description": "Captures summaries of medical consultations",
                "namespaces": ["medical/patient/{actorId}/{sessionId}"],
            },
        },
        {
            StrategyType.USER_PREFERENCE.value: {
                "name": "patient_preferences",
                "description": "Captures patient preferences and medical history",
                "namespaces": ["medical/patient/{actorId}/preferences"],
            },
        },
    ]
    
    try:
        print(f"🚀 Creating AgentCore memory: {memory_name}")
        
        # Create memory resource
        memory = memory_client.create_memory_and_wait(
            name=memory_name,
            strategies=strategies,
            description="Memory for medical assistant consultations",
            event_expiry_days=90,  # Keep medical conversations for 90 days
        )
        
        memory_id = memory["id"]
        print(f"✅ Memory created successfully: {memory_id}")
        
        # Store memory ID in SSM
        ssm.put_parameter(
            Name=ssm_param,
            Value=memory_id,
            Type="String",
            Overwrite=True
        )
        print(f"🔐 Stored memory_id in SSM: {ssm_param}")
        print("🎉 Medical assistant memory setup completed!")
        
        return memory_id
        
    except Exception as e:
        if "already exists" in str(e):
            print("📋 Memory already exists, finding existing resource...")
            memories = memory_client.list_memories()
            print(f"🔍 Found {len(memories)} memories")
            
            # Debug: print all memory names
            for memory in memories:
                print(f"  - Memory: {memory.get('name', 'No name')} (ID: {memory.get('id', 'No ID')})")
            
            # Try exact match first, then partial match
            memory_id = None
            for memory in memories:
                if memory.get("name") == memory_name:
                    memory_id = memory["id"]
                    break
            
            # If no exact match, try partial match
            if not memory_id:
                for memory in memories:
                    if memory_name.lower() in memory.get("name", "").lower():
                        memory_id = memory["id"]
                        break
            
            # If no match by name, use the first MedicalAssistant memory
            if not memory_id:
                for memory in memories:
                    memory_id_str = memory.get("id", "")
                    if "MedicalAssistant" in memory_id_str:
                        memory_id = memory_id_str
                        break
            
            if memory_id:
                print(f"✅ Using existing memory: {memory_id}")
                # Update SSM parameter
                ssm.put_parameter(
                    Name=ssm_param,
                    Value=memory_id,
                    Type="String",
                    Overwrite=True
                )
                print(f"🔐 Updated memory_id in SSM: {ssm_param}")
                return memory_id
            else:
                print("❌ Could not find existing memory resource")
                print("💡 Try deleting the existing memory and running again")
                raise
        else:
            print(f"❌ Error creating memory: {str(e)}")
            raise

if __name__ == "__main__":
    setup_medical_memory()