from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.parsers import JSONParser, MultiPartParser
from django.db import IntegrityError
from .models import Conversation, Message
from .serializers import ConversationTextSerializer, ConversationVoiceSerializer, MessageSerializer, ConversationListSerializer, MessageListSerializer
from core.chatgpt import get_chat_response
from core.voice import get_text_from_audio
from googletrans import Translator

class ChatbotTextView(APIView):
    parser_classes = [JSONParser]

    def post(self, request):
        serializer = ConversationTextSerializer(data=request.data, context = {'request': request})

        if serializer.is_valid():
            user_id = serializer.validated_data['user_id']
            input_text = serializer.validated_data['input_text']
            conversation_id = serializer.validated_data.get('conversation_id')
            language_pref = serializer.validated_data['language']

            message_user_type = 1 #user
            message_type = 1 #text

            # Check if a conversation with the provided ID exists; if not, create a new one
            if conversation_id:
                try:
                    conversation = Conversation.objects.get(id=conversation_id)
                except Conversation.DoesNotExist:
                    return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)
            else:
                try:
                    conversation = Conversation.objects.create(user_id=user_id)
                except IntegrityError as e:
                    return Response({'error': 'User not found'}, status=status.HTTP_400_BAD_REQUEST)

            messages = []

            # Create a new message within the conversation
            message_data = {
                'conversation_id': conversation.id,
                'type': message_type,
                'content': input_text,
                'message_user_type': message_user_type,
                'user_id': user_id
            }
            message_serializer = MessageSerializer(data=message_data)

            # Check if the message data is valid according to the MessageSerializer
            if message_serializer.is_valid():
                message_serializer.save()
                messages.append(message_serializer.validated_data)

                assistant_reply = get_chat_response(input_text)

                translator = Translator()
                translated_response = translator.translate(assistant_reply, dest=language_pref).text

                message_user_type = 2 #Bot

                # Create a response message and save it to the database
                response_data = {
                    'conversation_id': conversation.id,
                    'type': message_type,
                    'content': translated_response,
                    'message_user_type': message_user_type, 
                    'user_id': user_id
                }
                response_serializer = MessageSerializer(data=response_data)

                # Check if the response data is valid according to the MessageSerializer
                if response_serializer.is_valid():
                    response_serializer.save()
                    messages.append(response_serializer.validated_data)
                    response_data = {
                        'conversation_id': conversation.id,
                        'messages': messages 
                    }
                    return Response(response_data, status=status.HTTP_201_CREATED)
                else:
                    return Response(response_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(message_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

class ChatbotVoiceView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        serializer = ConversationVoiceSerializer(data=request.data, context = {'request': request})

        if serializer.is_valid():

            audio = serializer.validated_data['audio']
            user_id = serializer.validated_data['user_id']
            conversation_id = serializer.validated_data.get('conversation_id')
            language_pref = serializer.validated_data['language']
            audio_name = audio.name

            message_user_type = 1 #user
            message_type = 2 #audio

            # Check if a conversation with the provided ID exists; if not, create a new one
            if conversation_id:
                try:
                    conversation = Conversation.objects.get(id=conversation_id)
                except Conversation.DoesNotExist:
                    return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)
            else:
                try:
                    conversation = Conversation.objects.create(user_id=user_id)
                except IntegrityError as e:
                    return Response({'error': 'User not found'}, status=status.HTTP_400_BAD_REQUEST)

            messages = []

            # Create a new message within the conversation
            message_data = {
                'conversation_id': conversation.id,
                'type': message_type,
                'content': audio_name,
                'reference': audio,
                'message_user_type': message_user_type,
                'user_id': user_id
            }
            print(message_data)
            message_serializer = MessageSerializer(data=message_data)

            # Check if the message data is valid according to the MessageSerializer
            if message_serializer.is_valid():
                output = message_serializer.save()
                validated_data = message_serializer.validated_data
                validated_data["reference"] = output.reference.url
                print(validated_data)
                messages.append(validated_data)

                input_text = get_text_from_audio(validated_data["reference"])['text']
                print(input_text)
                assistant_reply = get_chat_response(input_text)
                print(assistant_reply)

                translator = Translator()
                translated_response = translator.translate(assistant_reply, dest=language_pref).text

                message_type = 1 #text
                message_user_type = 2 #Bot

                # Create a response message and save it to the database
                response_data = {
                    'conversation_id': conversation.id,
                    'type': message_type,
                    'content': translated_response,
                    'message_user_type': message_user_type, 
                    'user_id': user_id
                }
                response_serializer = MessageSerializer(data=response_data)

                # Check if the response data is valid according to the MessageSerializer
                if response_serializer.is_valid():
                    output = response_serializer.save()
                    validated_data = response_serializer.validated_data
                    messages.append(validated_data)
                    response_data = {
                        'conversation_id': conversation.id,
                        'messages': messages 
                    }
                    return Response(response_data, status=status.HTTP_201_CREATED)
                else:
                    return Response(response_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(message_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

class ConversationListView(generics.ListAPIView):
    parser_classes = [JSONParser]
    serializer_class = ConversationListSerializer

    def get_queryset(self):
        user_id = self.kwargs['user_id'] 
        return Conversation.objects.filter(user_id=user_id)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        conversations = serializer.data
        response_data = {
            "conversations": conversations
        }
        return Response(response_data)

    
class MessageListView(APIView):
    parser_classes = [JSONParser]
    
    def get(self, request, conversation_id):
        messages = Message.objects.filter(conversation__id=conversation_id)
        serializer = MessageListSerializer(messages, many=True)
        serialized_data = []
        for message in serializer.data:
            if message['reference']:
                message['reference'] = request.build_absolute_uri(message['reference'])

            serialized_data.append(message)

        response_data = {
            'messages': serialized_data,
        }
        return Response(response_data)