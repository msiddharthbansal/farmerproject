from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _
from .models import User, Product, Order, ProductReview

class UserSignupForm(UserCreationForm):
    user_type = forms.ChoiceField(
        choices=User.USER_TYPE_CHOICES,
        widget=forms.RadioSelect,
        label=_('I am a'),
        initial='consumer'
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'user_type', 'phone', 'address', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        # Add Bootstrap classes
        for field_name, field in self.fields.items():
            if field_name != 'user_type':
                field.widget.attrs['class'] = 'form-control'

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'address', 'profile_pic']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

class FarmerProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email', 'phone', 
            'address', 'profile_pic', 'npop_certificate_number', 
            'npop_certificate_issue_date', 'npop_certificate_expiry_date',
            'npop_certificate_file'
        ]
        widgets = {
            'npop_certificate_issue_date': forms.DateInput(attrs={'type': 'date'}),
            'npop_certificate_expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        
        # Add help texts for NPOP fields
        self.fields['npop_certificate_number'].help_text = 'Enter your NPOP certification number'
        self.fields['npop_certificate_issue_date'].help_text = 'Date when the certificate was issued'
        self.fields['npop_certificate_expiry_date'].help_text = 'Date when the certificate expires'
        self.fields['npop_certificate_file'].help_text = 'Upload a scanned copy or photo of your certificate'

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'category', 'unit', 
            'price', 'discount_price', 'quantity_available', 
            'is_organic', 'is_available', 'image',
            'harvest_date', 'expiry_date', 'nutritional_info'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'nutritional_info': forms.Textarea(attrs={'rows': 4}),
            'harvest_date': forms.DateInput(attrs={'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes
        for field_name, field in self.fields.items():
            if field_name not in ['is_organic', 'is_available']:
                field.widget.attrs['class'] = 'form-control'
            else:
                field.widget.attrs['class'] = 'form-check-input'

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['quantity', 'shipping_address']
        widgets = {
            'shipping_address': forms.Textarea(attrs={'rows': 3}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
    
    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity <= 0:
            raise forms.ValidationError(_('Quantity must be greater than zero.'))
        return quantity 

class ProductReviewForm(forms.ModelForm):
    rating = forms.ChoiceField(
        choices=ProductReview.RATING_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'star-rating-input'}),
        required=True
    )
    review_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': _('Share your experience with this product...')
        }),
        required=True
    )
    
    class Meta:
        model = ProductReview
        fields = ['rating', 'review_text'] 