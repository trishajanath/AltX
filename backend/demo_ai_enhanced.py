"""
Demo: AI-Enhanced vs Template-Based Code Generation
Shows the difference between static templates and AI-driven customization
"""

import asyncio
import json
from pathlib import Path
from ai_enhanced_generator import AIEnhancedGenerator

async def demo_ai_enhanced_generation():
    """Demonstrate AI-enhanced code generation with custom requirements"""
    
    print("🎯 AI-Enhanced Code Generation Demo")
    print("=" * 50)
    
    generator = AIEnhancedGenerator()
    
    # Test various complex user ideas that go beyond basic templates
    test_ideas = [
        {
            "idea": "A todo app where tasks can have priority levels (low, medium, high), due dates, and can be assigned to team members. Show overdue tasks in red and allow bulk status updates.",
            "name": "Team Task Manager"
        },
        {
            "idea": "A chat application with file sharing, message reactions (emoji), and the ability to create separate channels for different topics.",
            "name": "Team Chat Plus"
        },
        {
            "idea": "An ecommerce store for handmade crafts where products can have multiple photos, customer reviews with star ratings, and a wishlist feature.",
            "name": "Craft Store"
        }
    ]
    
    for i, test_case in enumerate(test_ideas, 1):
        print(f"\n🧪 Test Case {i}: {test_case['name']}")
        print(f"💭 User Idea: {test_case['idea']}")
        print("\n🤖 AI Analysis Phase...")
        
        # Analyze the idea (this would normally call OpenAI)
        plan = await generator.analyze_user_idea(test_case['idea'])
        
        print(f"📊 Detected App Type: {plan.app_type}")
        print(f"📝 Generated Name: {plan.name}")
        print(f"🎨 Custom Features: {len(plan.features)}")
        print(f"🔧 Custom UI Requirements: {len(plan.ui_requirements)}")
        
        # Show what custom fields would be added
        for model in plan.models:
            custom_fields = [f for f in model.fields if f.name not in ['id', 'title', 'description', 'created_at', 'updated_at']]
            if custom_fields:
                print(f"🆕 Custom fields for {model.name}: {[f.name for f in custom_fields]}")
        
        print("-" * 40)

async def compare_generation_approaches():
    """Compare template-based vs AI-enhanced generation"""
    
    print("\n🔄 Comparison: Template vs AI-Enhanced")
    print("=" * 50)
    
    user_idea = "A todo app with priority levels, due dates, and project organization"
    
    print(f"📝 User Idea: {user_idea}")
    
    # Template-based approach (current enhanced_generator)
    print("\n🏭 Template-Based Approach:")
    print("✅ Fast and reliable")
    print("✅ No API costs")
    print("✅ Consistent output")
    print("❌ Limited to predefined features")
    print("❌ Cannot understand 'priority levels' or 'due dates'")
    print("❌ Same output for any todo app idea")
    print("📤 Output: Basic todo app with title, description, completed")
    
    # AI-Enhanced approach
    print("\n🤖 AI-Enhanced Approach:")
    print("✅ Understands custom requirements")
    print("✅ Generates tailored code")
    print("✅ Extends templates intelligently")
    print("✅ Scalable to any complexity")
    print("❌ Requires API access")
    print("❌ Slightly slower")
    print("❌ Depends on AI service availability")
    
    generator = AIEnhancedGenerator()
    plan = await generator.analyze_user_idea(user_idea)
    
    print("📤 Output: Todo app with custom fields:")
    for model in plan.models:
        print(f"   - {model.name} model with {len(model.fields)} fields")
        for field in model.fields:
            if field.name not in ['id', 'created_at', 'updated_at']:
                print(f"     • {field.name}: {field.type}")

def demonstrate_template_evolution():
    """Show how templates can be used as AI seeds"""
    
    print("\n🌱 Template Evolution Strategy")
    print("=" * 50)
    
    print("💡 Best of Both Worlds:")
    print("1. 🏗️  Start with reliable template foundations")
    print("2. 🤖 Use AI to analyze user requirements")
    print("3. ⚡ Enhance templates with custom features")
    print("4. 🔒 Maintain array safety and error handling")
    print("5. 🎯 Generate truly customized applications")
    
    print("\n🔄 Process Flow:")
    print("User Idea → AI Analysis → Template Selection → AI Enhancement → Custom Code")
    
    print("\n📊 Benefits:")
    print("✅ Reliability of templates + Flexibility of AI")
    print("✅ Custom features without starting from scratch")
    print("✅ Maintained code quality and safety patterns")
    print("✅ Scalable to unlimited complexity")
    print("✅ Graceful fallback when AI is unavailable")

async def show_generated_code_samples():
    """Show examples of what the AI-enhanced generator would produce"""
    
    print("\n📝 Generated Code Samples")
    print("=" * 50)
    
    print("🎯 For: 'Todo app with priority levels and due dates'")
    print("\n📄 Generated Pydantic Model:")
    
    sample_model = '''class TaskBase(BaseModel):
    title: str = Field(description="Task title")
    description: Optional[str] = Field(default=None, description="Task description")
    completed: bool = Field(default=False)
    priority: Literal['low', 'medium', 'high'] = Field(default='medium', description="Task priority level")
    due_date: Optional[date] = Field(default=None, description="Task due date")
    project_id: Optional[int] = Field(default=None, description="Associated project ID")

class Task(TaskBase):
    id: int
    created_at: datetime
    updated_at: datetime
    is_overdue: bool = Field(description="Computed field for overdue status")'''
    
    print(sample_model)
    
    print("\n⚛️ Enhanced React Component:")
    
    sample_component = '''function TaskItem({ task, onUpdate, onDelete }) {
  const isOverdue = task.due_date && new Date(task.due_date) < new Date() && !task.completed
  
  const priorityColors = {
    low: 'text-green-600 bg-green-50',
    medium: 'text-yellow-600 bg-yellow-50', 
    high: 'text-red-600 bg-red-50'
  }
  
  return (
    <div className={`card p-4 ${isOverdue ? 'border-red-300 bg-red-50' : ''}`}>
      <div className="flex items-center gap-3">
        {/* Priority indicator */}
        <span className={`px-2 py-1 text-xs rounded-full ${priorityColors[task.priority]}`}>
          {task.priority.toUpperCase()}
        </span>
        
        {/* Task content */}
        <div className="flex-1">
          <h3 className={task.completed ? 'line-through text-gray-500' : 'text-gray-900'}>
            {task.title}
          </h3>
          {task.due_date && (
            <p className={`text-sm ${isOverdue ? 'text-red-600' : 'text-gray-500'}`}>
              Due: {formatDate(task.due_date)}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}'''
    
    print(sample_component)

async def main():
    """Run all demonstrations"""
    await demo_ai_enhanced_generation()
    await compare_generation_approaches()
    demonstrate_template_evolution()
    await show_generated_code_samples()
    
    print("\n🎉 Demo Complete!")
    print("\n💡 Key Takeaways:")
    print("1. Templates provide reliability, AI provides customization")
    print("2. The hybrid approach gets the best of both worlds")
    print("3. Users get truly personalized applications")
    print("4. Code quality and safety are maintained")
    print("5. The system gracefully handles AI unavailability")

if __name__ == "__main__":
    asyncio.run(main())