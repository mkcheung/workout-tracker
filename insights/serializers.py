from rest_framework import serializers

class InsightsDateRangeQuerySerializer(serializers.Serializer):
    performed_from = serializers.DateField(required=False, input_formats=["%Y-%m-%d"])
    performed_to = serializers.DateField(required=False, input_formats=["%Y-%m-%d"])
    exercise_id = serializers.IntegerField(required=True)
    metric = serializers.ChoiceField(choices=['top_set_weight', 'estimated_1rm', 'tonnage'])

    def validate(self, attrs):
        perform_from = attrs.get('performed_from')
        perform_to = attrs.get('performed_to')
        if perform_from and perform_to and perform_from > perform_to:
            raise serializers.ValidationError("From Date cannot be greater than the To Date.")
        
        return attrs

    