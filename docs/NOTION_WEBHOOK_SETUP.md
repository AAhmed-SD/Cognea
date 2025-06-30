# Notion Webhook Setup Guide

This guide explains how to set up Notion webhooks to automatically sync content with Cognie when pages or databases are updated.

## Overview

Notion webhooks allow Cognie to receive real-time notifications when content changes in your Notion workspace. This enables automatic flashcard generation and synchronization without manual intervention.

## Webhook Events We Listen For

Cognie listens for the following Notion webhook events:

- `page.updated` - When a page is modified
- `database.updated` - When a database is modified
- `page.created` - When a new page is created
- `database.created` - When a new database is created

## Prerequisites

1. **Notion Integration**: You must have a Notion integration set up with API access
2. **Public Endpoint**: Your Cognie instance must be accessible via HTTPS
3. **Webhook Secret**: A secret key for verifying webhook authenticity

## Step 1: Create Notion Integration

1. Go to [Notion Integrations](https://www.notion.so/my-integrations)
2. Click "New integration"
3. Give it a name (e.g., "Cognie AI")
4. Select your workspace
5. Set capabilities:
   - Read content
   - Update content (if you want bidirectional sync)
6. Copy the **Internal Integration Token**

## Step 2: Configure Environment Variables

Add these to your `.env.production` file:

```bash
# Notion Integration
NOTION_CLIENT_ID=your_notion_client_id
NOTION_CLIENT_SECRET=your_notion_client_secret
NOTION_WEBHOOK_SECRET=your_webhook_secret_key
NOTION_RATE_LIMIT_PER_MINUTE=3
NOTION_MAX_RETRIES=3
```

## Step 3: Set Up Webhook Endpoint

### Option A: Using Notion's Webhook Service (Recommended)

1. Go to [Notion Webhooks](https://www.notion.so/webhooks)
2. Click "Create webhook"
3. Configure the webhook:
   - **Name**: Cognie Sync
   - **URL**: `https://your-domain.com/api/notion/webhook/notion`
   - **Events**: Select the events you want to listen for
   - **Parent**: Choose specific pages/databases or entire workspace
4. Copy the **Webhook Secret** and add it to your environment variables

### Option B: Manual Webhook Setup

If you prefer to set up webhooks manually via API:

```bash
curl -X POST https://api.notion.com/v1/webhooks \
  -H "Authorization: Bearer YOUR_INTEGRATION_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": {
      "type": "page_id",
      "page_id": "YOUR_PAGE_ID"
    },
    "events": ["page.updated", "database.updated"],
    "url": "https://your-domain.com/api/notion/webhook/notion"
  }'
```

## Step 4: Verify Webhook Setup

1. **Test the verification endpoint**:
   ```bash
   curl "https://your-domain.com/api/notion/webhook/notion/verify?challenge=test123"
   ```
   Should return: `{"challenge": "test123"}`

2. **Test webhook signature verification**:
   ```bash
   curl -X POST https://your-domain.com/api/notion/webhook/notion \
     -H "Content-Type: application/json" \
     -H "X-Notion-Signature: sha256=YOUR_SIGNATURE" \
     -d '{"type": "page.updated", "page": {"id": "test"}}'
   ```

## Step 5: Configure User Authentication

Users need to authenticate their Notion account with Cognie:

1. **Frontend Integration**: Add a "Connect Notion" button that calls `/api/notion/auth`
2. **API Key Storage**: Store the user's Notion API key securely in the database
3. **Permission Setup**: Guide users to share pages/databases with your integration

## Webhook Processing Flow

1. **Webhook Received**: Notion sends webhook to `/api/notion/webhook/notion`
2. **Signature Verification**: Cognie verifies the webhook signature
3. **Event Processing**: Extracts page/database ID and event type
4. **User Discovery**: Finds all users who have synced this content
5. **Queue Sync**: Adds sync operation to rate-limited queue
6. **Debounce Check**: Prevents duplicate syncs for rapid changes
7. **Sync Execution**: Generates flashcards and updates database

## Security Considerations

### Webhook Signature Verification

Cognie verifies webhook signatures to prevent unauthorized requests:

```python
def verify_notion_webhook_signature(body: bytes, signature: str, secret: str) -> bool:
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(f"sha256={expected_signature}", signature)
```

### Rate Limiting

- **Notion API**: 3 requests per minute per user
- **Webhook Processing**: Queued to prevent overwhelming the API
- **Debouncing**: 30-second cooldown between syncs for the same content

### Error Handling

- **Invalid Signatures**: Return 401 Unauthorized
- **Processing Errors**: Log errors and return 500 Internal Server Error
- **Rate Limit Exceeded**: Queue requests for later processing

## Monitoring and Debugging

### Logs to Monitor

```bash
# Webhook reception
grep "Received Notion webhook" /var/log/personal-agent/app.log

# Sync operations
grep "Internal sync completed" /var/log/personal-agent/app.log

# Errors
grep "Error processing Notion webhook" /var/log/personal-agent/app.log
```

### Health Checks

1. **Webhook Endpoint**: `GET /api/notion/webhook/notion/verify`
2. **Sync Status**: `GET /api/notion/sync-status/{page_id}`
3. **Queue Status**: Check Redis for queued operations

### Common Issues

1. **Webhook Not Received**:
   - Check HTTPS endpoint accessibility
   - Verify webhook URL is correct
   - Check firewall/network settings

2. **Signature Verification Fails**:
   - Verify `NOTION_WEBHOOK_SECRET` is correct
   - Check webhook secret in Notion dashboard
   - Ensure signature header is present

3. **Sync Not Triggered**:
   - Verify user has authenticated with Notion
   - Check if page/database is shared with integration
   - Review rate limiting settings

## Testing Webhooks Locally

For development, you can use tools like ngrok to expose your local server:

```bash
# Install ngrok
npm install -g ngrok

# Expose local server
ngrok http 8000

# Use the ngrok URL in your webhook configuration
# https://abc123.ngrok.io/api/notion/webhook/notion
```

## Production Deployment

1. **SSL Certificate**: Ensure HTTPS is properly configured
2. **Load Balancer**: Set up proper load balancing for webhook endpoints
3. **Monitoring**: Set up alerts for webhook failures
4. **Backup**: Implement webhook retry mechanisms
5. **Scaling**: Consider using message queues for high-volume webhooks

## Troubleshooting

### Webhook Not Working

1. Check webhook URL is accessible
2. Verify signature verification
3. Check user authentication status
4. Review rate limiting settings
5. Check logs for errors

### Sync Not Happening

1. Verify page/database permissions
2. Check user's Notion API key
3. Review debounce settings
4. Check queue processing
5. Verify AI service is working

### Performance Issues

1. Monitor queue size
2. Check rate limiting
3. Review database performance
4. Optimize flashcard generation
5. Consider caching strategies

## Support

If you encounter issues:

1. Check the logs for detailed error messages
2. Verify all environment variables are set correctly
3. Test webhook endpoints manually
4. Review Notion API documentation
5. Contact support with specific error details 