"""
Chatbot Management Script
Use this script to control and test the chatbot functionality
"""

import sys
import os
import argparse

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_basic_functionality():
    """Test basic conversational AI without Selenium"""
    print("Testing Basic Conversational AI...")
    print("=" * 50)
    
    try:
        from conversational_ai import ConversationalAI
        
        ai = ConversationalAI()
        ai.toggle_selenium_chatbot(False)  # Ensure Selenium is disabled
        
        test_messages = [
            "Hello! I'm learning English.",
            "How are you today?",
            "I need help with conversation practice.",
            "Thank you for your help!"
        ]
        
        for message in test_messages:
            print(f"\nUser: {message}")
            response = ai.get_response(message, 'general')
            print(f"AI: {response}")
        
        stats = ai.get_conversation_stats()
        print(f"\nConversation Statistics:")
        print(f"Messages exchanged: {stats['messages_exchanged']}")
        print(f"Selenium active: {stats.get('selenium_chatbot_active', False)}")
        
        ai.cleanup()
        print("\n✓ Basic functionality test passed!")
        return True
        
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        return False

def test_selenium_functionality():
    """Test Selenium chatbot functionality"""
    print("Testing Selenium Chatbot...")
    print("=" * 50)
    
    try:
        # Enable Selenium for this test
        from chatbot_config import ChatbotConfig
        ChatbotConfig.enable_selenium_chatbot()
        
        from conversational_ai import ConversationalAI
        
        ai = ConversationalAI()
        
        if ai.selenium_chatbot and ai.selenium_chatbot.is_ready():
            print("✓ Selenium chatbot is ready!")
            
            test_message = "Hello! I'm learning English and would like to practice conversation."
            print(f"\nUser: {test_message}")
            response = ai.get_response(test_message, 'general')
            print(f"AI: {response}")
            
            ai.cleanup()
            print("\n✓ Selenium functionality test passed!")
            return True
        else:
            print("⚠ Selenium chatbot not ready, testing fallback...")
            response = ai.get_response("Hello!", 'general')
            print(f"Fallback response: {response}")
            ai.cleanup()
            return True
            
    except Exception as e:
        print(f"✗ Selenium functionality test failed: {e}")
        return False

def interactive_chat():
    """Start an interactive chat session"""
    print("Interactive Chat Session")
    print("=" * 50)
    print("Type 'quit' to exit, 'toggle' to switch between Selenium and fallback mode")
    print()
    
    try:
        from conversational_ai import ConversationalAI
        from chatbot_config import ChatbotConfig
        
        ai = ConversationalAI()
        selenium_enabled = ChatbotConfig.ENABLE_SELENIUM_CHATBOT
        
        print(f"Chatbot mode: {'Selenium' if selenium_enabled else 'Fallback'}")
        print()
        
        while True:
            user_input = input("You: ").strip()
            
            if user_input.lower() == 'quit':
                break
            elif user_input.lower() == 'toggle':
                selenium_enabled = not selenium_enabled
                ai.toggle_selenium_chatbot(selenium_enabled)
                print(f"Switched to: {'Selenium' if selenium_enabled else 'Fallback'} mode")
                continue
            elif not user_input:
                continue
            
            response = ai.get_response(user_input, 'general')
            print(f"AI: {response}")
            print()
        
        ai.cleanup()
        print("Chat session ended.")
        
    except KeyboardInterrupt:
        print("\nChat session interrupted.")
    except Exception as e:
        print(f"Error in interactive chat: {e}")

def show_config():
    """Show current configuration"""
    print("Current Chatbot Configuration")
    print("=" * 50)
    
    try:
        from chatbot_config import ChatbotConfig
        
        config = ChatbotConfig.get_config()
        for key, value in config.items():
            print(f"{key}: {value}")
            
    except Exception as e:
        print(f"Error loading configuration: {e}")

def main():
    parser = argparse.ArgumentParser(description='Chatbot Management Script')
    parser.add_argument('action', choices=['test', 'test-selenium', 'chat', 'config'], 
                       help='Action to perform')
    
    args = parser.parse_args()
    
    if args.action == 'test':
        test_basic_functionality()
    elif args.action == 'test-selenium':
        test_selenium_functionality()
    elif args.action == 'chat':
        interactive_chat()
    elif args.action == 'config':
        show_config()

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # If no arguments provided, show help and run basic test
        print("Chatbot Management Script")
        print("Usage: python chatbot_manager.py [test|test-selenium|chat|config]")
        print()
        print("Running basic test...")
        test_basic_functionality()
    else:
        main()
