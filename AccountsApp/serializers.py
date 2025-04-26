from rest_framework import serializers
from django.contrib.auth.models import User

class SzSignup(serializers.ModelSerializer):
    class Meta():
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'password']
        # لاجبار المستحدم على ادخال هذه الحقول
        extra_kwargs = {
            'username':{
                'required':True
                , 'allow_blank':False}
            ,'first_name':{
                'required':True
                , 'allow_blank':False}
            ,'last_name':{
                'required':True
                , 'allow_blank':False}
            ,'email':{
                'required':True
                , 'allow_blank':False}
            ,'password':{
                'required':True
                , 'allow_blank':False
                , 'min_length':8}
            
            , 'write_only': True  # يمنع إرسال كلمة المرور في الردود
        }
class SzUsers(serializers.ModelSerializer):
    class Meta():
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'username', 'password')