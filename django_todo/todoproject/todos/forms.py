from django import forms
from .models import todo

class TodoForm(forms.ModelForm):
    class Meta:
        model = todo
        
        fields = ['title', 'description', 'due_date', 'category', 'completed']
        
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input', 
                'placeholder': 'What needs to be done?'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-input', 
                'placeholder': 'Add details (optional)', 
                'rows': 3
            }),
            'due_date': forms.DateInput(
                format='%Y-%m-%d',
                attrs={
                    'class': 'form-input', 
                    'type': 'date'
                }
            ),
            'category': forms.Select(attrs={
                'class': 'form-input'
            }),
            'completed': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
        }
