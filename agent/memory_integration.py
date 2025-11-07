#!/usr/bin/env python3
"""
Direct Memory Integration for Medical Assistant
Safe approach without hooks to avoid runtime issues
"""

import boto3
import os
from bedrock_agentcore.memory import MemoryClient
from typing import List, Dict, Any, Optional


class MedicalMemoryManager:
    """Direct memory integration for medical assistant"""
    
    def __init__(self):
        self.memory_client = MemoryClient()
        self.memory_id = self._get_memory_id()
        self.actor_id = "medical_patient"  # Default actor ID
        self.session_id = "consultation"   # Default session ID
        
    def _get_memory_id(self) -> str:
        """Get memory ID from SSM parameter"""
        try:
            ssm = boto3.client('ssm')
            response = ssm.get_parameter(Name="/app/medicalassistant/agentcore/memory_id")
            return response['Parameter']['Value']
        except Exception as e:
            print(f"Warning: Could not get memory ID from SSM: {e}")
            return None
    
    def set_session_context(self, actor_id: str = None, session_id: str = None):
        """Set actor and session IDs for memory context"""
        if actor_id:
            self.actor_id = actor_id
        if session_id:
            self.session_id = session_id
    
    def get_conversation_context(self, k: int = 5) -> List[Dict[str, Any]]:
        """Load recent conversation history"""
        if not self.memory_id:
            return []
            
        try:
            recent_turns = self.memory_client.get_last_k_turns(
                memory_id=self.memory_id,
                actor_id=self.actor_id,
                session_id=self.session_id,
                k=k,
            )
            
            context_messages = []
            for turn in recent_turns:
                for message in turn:
                    role = "assistant" if message["role"] == "ASSISTANT" else "user"
                    content = message["content"]["text"]
                    context_messages.append({
                        "role": role, 
                        "content": [{"text": content}]
                    })
            
            return context_messages
            
        except Exception as e:
            print(f"Memory load error: {e}")
            return []
    
    def get_user_context(self, query: str) -> str:
        """Get relevant user facts and preferences"""
        if not self.memory_id:
            return ""
            
        context_parts = []
        
        try:
            # Get user preferences
            preferences = self.memory_client.retrieve_memories(
                memory_id=self.memory_id,
                namespace=f"medical/patient/{self.actor_id}/preferences",
                query=query,
                top_k=3
            )
            
            if preferences:
                context_parts.append("\n**Patient Preferences:**")
                for pref in preferences:
                    context_parts.append(f"- {pref['content']['text']}")
            
            # Get user facts
            facts = self.memory_client.retrieve_memories(
                memory_id=self.memory_id,
                namespace=f"medical/patient/{self.actor_id}/facts",
                query=query,
                top_k=3
            )
            
            if facts:
                context_parts.append("\n**Patient Facts:**")
                for fact in facts:
                    context_parts.append(f"- {fact['content']['text']}")
                    
        except Exception as e:
            print(f"Context retrieval error: {e}")
        
        return "\n".join(context_parts) if context_parts else ""
    
    def save_conversation_turn(self, user_message: str, assistant_message: str):
        """Save a conversation turn to memory"""
        if not self.memory_id:
            return
            
        try:
            messages = [
                (user_message, "user"),
                (assistant_message, "assistant")
            ]
            
            self.memory_client.save_conversation(
                memory_id=self.memory_id,
                actor_id=self.actor_id,
                session_id=self.session_id,
                messages=messages,
            )
            
        except Exception as e:
            print(f"Memory save error: {e}")
    
    def save_user_message(self, message: str):
        """Save just a user message"""
        if not self.memory_id:
            return
            
        try:
            self.memory_client.save_conversation(
                memory_id=self.memory_id,
                actor_id=self.actor_id,
                session_id=self.session_id,
                messages=[(message, "user")],
            )
        except Exception as e:
            print(f"Memory save error: {e}")
    
    def save_assistant_message(self, message: str):
        """Save just an assistant message"""
        if not self.memory_id:
            return
            
        try:
            self.memory_client.save_conversation(
                memory_id=self.memory_id,
                actor_id=self.actor_id,
                session_id=self.session_id,
                messages=[(message, "assistant")],
            )
        except Exception as e:
            print(f"Memory save error: {e}")


# Global memory manager instance
memory_manager = MedicalMemoryManager()