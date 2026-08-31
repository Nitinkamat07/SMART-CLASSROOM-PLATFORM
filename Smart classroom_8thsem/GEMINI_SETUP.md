# 🤖 Gemini AI Chatbot Integration Guide

## 🚀 Quick Start

### Option 1: Standalone Chatbot (Recommended)
1. Open `gemini_chatbot.html` in your browser
2. Replace the API key in the file with your own Gemini API key
3. Start chatting with the AI assistant!

### Option 2: Get Your Free Gemini API Key

1. **Visit Google AI Studio**
   - Go to: https://makersuite.google.com/app/apikey
   - Sign in with your Google account

2. **Create API Key**
   - Click "Create API Key"
   - Copy your API key

3. **Add API Key**
   - Open `gemini_chatbot.html`
   - Find line: `const GEMINI_API_KEY = 'YOUR_API_KEY_HERE';`
   - Replace with your actual key: `const GEMINI_API_KEY = 'your-actual-key';`

4. **Open and Use**
   - Double-click `gemini_chatbot.html`
   - Start chatting with real AI!

## ✨ Features

### Real Gemini AI Integration
- ✅ Powered by Google's Gemini Pro model
- ✅ Natural language understanding
- ✅ Context-aware responses
- ✅ Real-time conversation

### Smart Classroom Context
- ✅ Knows about classroom availability
- ✅ Understands schedules and timetables
- ✅ Provides attendance information
- ✅ Faculty contact details
- ✅ General academic queries

### User Experience
- ✅ Beautiful modern UI
- ✅ Typing indicators
- ✅ Quick action buttons
- ✅ Smooth animations
- ✅ Mobile responsive

## 💬 Example Queries

Try asking:
- "What classrooms are available right now?"
- "Show me today's schedule"
- "What's my attendance percentage?"
- "How do I contact Dr. Smith?"
- "When is my next class?"
- "Which rooms have projectors?"
- "What's the capacity of room A101?"

## 🔧 Customization

### Update System Context
Edit the `systemContext` variable in `gemini_chatbot.html` to add:
- Your actual classroom data
- Real schedules
- Faculty information
- Custom rules and policies

### Styling
Modify the CSS in the `<style>` section to match your branding.

## 🌐 Integration with Main Website

To integrate with `index.html`:
1. Copy the Gemini API integration code
2. Replace the existing chatbot JavaScript
3. Update the API key
4. Test the integration

## 📝 Notes

- **Free Tier**: Gemini API offers generous free tier
- **Rate Limits**: 60 requests per minute
- **No Backend Required**: Works entirely in browser
- **Privacy**: Messages sent to Google's API

## 🎯 Production Deployment

For production:
1. Store API key securely (environment variables)
2. Implement rate limiting
3. Add error handling
4. Monitor API usage
5. Consider caching responses

## 🆘 Troubleshooting

**API Key Error?**
- Verify key is correct
- Check API is enabled in Google Cloud Console
- Ensure no extra spaces in key

**No Response?**
- Check internet connection
- Verify API quota not exceeded
- Check browser console for errors

**CORS Error?**
- Gemini API supports direct browser calls
- No proxy needed for this implementation

---

**Ready to use! Just add your API key and start chatting with real AI!** 🚀