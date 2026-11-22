# CIUX Birthday Assistant – Testing Documentation

## 1. Introduction

This document describes the testing performed on the CIUX Birthday Assistant, which was developed through five progressive versions (V1–V5). Testing focuses on birthday information retrieval, query understanding, intent recognition, dialogue context, LLM-based understanding, and voice interaction.

## 2. Testing Objectives

- Verify the assistant correctly processes user queries.
- Verify birthday information is retrieved from the dataset.
- Test intent recognition and entity extraction.
- Test conversational context and follow-up questions.
- Evaluate LLM-based query understanding.
- Test voice input and output in V5.
- Identify incorrect responses and unexpected behavior.

## 3. Test Cases

### V1 – Basic Rule-Based Chatbot

| Test ID | Test Input | Expected Result |
|---|---|---|
| TC01 | Hi | Assistant responds with a greeting. |
| TC02 | Hello | Assistant responds appropriately. |
| TC03 | Help | Assistant displays available capabilities. |
| TC04 | Whose birthday is today? | Displays today's birthday information if available. |
| TC05 | Show all birthdays | Displays available birthday records. |
| TC06 | Birthday in September | Displays September birthdays. |
| TC07 | When is Rahul's birthday? | Displays Rahul's birthday if found in the dataset. |
| TC08 | Bye | Assistant responds with a farewell. |

### V2 – Rule-Based NLU

| Test ID | Test Input | Expected Result |
|---|---|---|
| TC09 | List birthdays in October | Recognizes the month and retrieves October birthdays. |
| TC10 | Who has a birthday in January? | Identifies January and retrieves matching records. |
| TC11 | Tell me the birthday of Ananya | Identifies the person's name and retrieves the record. |
| TC12 | Show birthdays next month | Processes the month-related query. |
| TC13 | Birthday details of Kiran | Identifies the person and retrieves birthday information. |
| TC14 | Are there any birthdays in June? | Returns matching records or an appropriate no-data response. |
| TC15 | Show people living in Davangere | Retrieves matching location information if supported. |
| TC16 | Find birthday information | Recognizes a birthday-related request. |

### V3 – Dialogue Management

| Test ID | Test Input | Expected Result |
|---|---|---|
| TC17 | When is my nephew's birthday? | Assistant returns matching nephew information or asks for clarification. |
| TC18 | What about October? | Uses previous conversation context to process October. |
| TC19 | Birthdays in September | Retrieves September birthday records. |
| TC20 | What about nieces? | Uses context and filters niece-related information. |
| TC21 | When is my nephew's birthday? | Retrieves nephew information. |
| TC22 | Nikhil | Uses previous context to resolve the follow-up if applicable. |
| TC23 | Reset the conversation | Clears the dialogue context. |
| TC24 | What about October? after reset | Does not use cleared context and handles the query appropriately. |

### V4 – LLM-Based NLU

| Test ID | Test Input | Expected Result |
|---|---|---|
| TC25 | Can you tell me who celebrates a birthday this month? | Understands the month-based birthday query. |
| TC26 | I want to know whose birthday falls in September. | Interprets the query semantically. |
| TC27 | Find the birthday of Rahul. | Identifies the person and retrieves matching data. |
| TC28 | Are there any birthdays coming soon? | Interprets the upcoming-birthday query appropriately. |
| TC29 | Tell me about people born in December. | Retrieves matching December records. |
| TC30 | Who in my family has a birthday in March? | Processes family and month-related information. |
| TC31 | Show me Ananya's birthday details. | Identifies the person and retrieves matching information. |
| TC32 | Find birthday information for someone not in the dataset. | Provides a no-match response without inventing information. |

### V5 – Voice Assistant

| Test ID | Test Input | Expected Result |
|---|---|---|
| TC33 | Type "Hello" in the chat. | Displays an assistant greeting. |
| TC34 | Use microphone and say "Show birthdays in October." | Speech is converted into text and processed. |
| TC35 | Ask "When is Rahul's birthday?" using voice. | Assistant processes the voice query and responds. |
| TC36 | Enable voice output. | Assistant speaks its response if speech synthesis is supported. |
| TC37 | Disable voice output. | Assistant responses are displayed without speaking. |
| TC38 | Stop speech playback. | Speech stops when the stop function is activated. |
| TC39 | Deny microphone permission. | Displays or handles the microphone permission error appropriately. |
| TC40 | Ask a birthday question using voice in a noisy environment. | Handles recognition limitations or requests the user to repeat. |

## 4. Testing Summary

The test cases cover the major functionality of the five versions of the CIUX Birthday Assistant. Testing includes basic chatbot responses, natural language understanding, birthday information retrieval, dialogue context management, LLM integration, and voice interaction.

Actual test results should be recorded after executing each test case.

## 5. Conclusion

Testing helps evaluate the progressive development of the CIUX Birthday Assistant from a basic rule-based chatbot to a conversational AI assistant with context awareness, LLM-based query understanding, and voice interaction.

The test cases provide a structured method for checking functionality, identifying issues, and improving the overall conversational user experience.