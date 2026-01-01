export interface ChatMessage {
  text: string;
  language: string;
  color: 'blue' | 'green' | 'red' | 'black';
  sender: 'person1' | 'person2' | 'person3';
  sentiment: string;
  timestamp?: number;
}

export interface PersonConfig {
  id: 'person1' | 'person2' | 'person3';
  name: string;
  language: string;
  languageCode: string;
}

