from rest_framework import generics,serializers,permissions
from .models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
class UserSerializer(serializers.ModelSerializer):
 class Meta:
  model=User;fields=['id','username','email','password'];extra_kwargs={'password':{'write_only':True}}
 def validate(self,attrs):
  try: validate_password(attrs['password'],user=User(username=attrs.get('username',''),email=attrs.get('email','')))
  except DjangoValidationError as exc: raise serializers.ValidationError({'password':list(exc.messages)})
  return attrs
 def create(self,validated_data): return User.objects.create_user(**validated_data)
class RegisterView(generics.CreateAPIView):
 queryset=User.objects.all();serializer_class=UserSerializer;permission_classes=[permissions.AllowAny]
class MeView(generics.RetrieveAPIView):
 serializer_class=UserSerializer
 def get_object(self): return self.request.user
