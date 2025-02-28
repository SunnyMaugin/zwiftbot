# Discord Bot Command Guide

## Administrative Commands

### 🔄 Sync Commands
- `/sync` - Sync all slash commands to Discord
- `!sync` - Alternative sync method (bot owner only)
  ```
  Usage: /sync
  Purpose: Updates all slash commands in your server
  ```

### 🔑 Key Management

#### Adding Keys
- `/addkeys` - Add individual keys
  ```
  Usage: /addkeys product_id:215075 keys:KEY1-XXXX,KEY2-XXXX
  Purpose: Add one or more keys manually
  ```

- `/importkeys` - Bulk import keys from file
  ```
  Usage: /importkeys product_id:215075 file:[attach .txt file]
  Purpose: Import multiple keys from a text file
  Note: File should contain one key per line
  ```

#### Viewing Keys
- `/checkkeys` - Check remaining keys for all products
  ```
  Usage: /checkkeys
  Purpose: Shows how many keys are left for each product
  ```

- `/viewkeys` - View specific product keys with pagination
  ```
  Usage: /viewkeys product_id:215075 page:1 keys_per_page:10
  Purpose: View actual keys for a specific product
  ```

- `/searchkeys` - Search for specific keys
  ```
  Usage: /searchkeys search_term:XXXX [product_id:215075]
  Purpose: Find keys containing specific text
  ```

#### Key Statistics and History
- `/keystats` - View detailed key statistics
  ```
  Usage: /keystats [product_id:215075]
  Purpose: Shows usage statistics, charts, and low stock warnings
  ```

- `/keyhistory` - View key usage history
  ```
  Usage: /keyhistory [lines:10]
  Purpose: Shows recent key assignments and usage
  ```

#### Backup Management
- `/restorekeys` - Restore keys from backup
  ```
  Usage: /restorekeys
  Purpose: Restore keys from the most recent backup
  ```

## User Commands

### 💳 Purchase Commands
- `/buy` - Purchase a product
  ```
  Usage: /buy product:[select from menu]
  Purpose: Start the purchase process for a product
  Note: Will show variant selection if available
  ```

### 📋 Order Management
- `/status` - Check order status
  ```
  Usage: /status
  Purpose: Check the status of your latest invoice
  Note: Has a 30-second cooldown
  ```

### ⚙️ Utility Commands
- `/ping` - Check bot latency
  ```
  Usage: /ping
  Purpose: Check if bot is responsive and view latency
  ```

## File Formats

### Key Import File (for /importkeys)

## Notes
- All administrative commands require appropriate permissions
- All responses to administrative commands are ephemeral (only visible to the command user)
- The bot automatically backs up keys before any modifications
- Keys are automatically delivered when a purchase is completed
- Low stock warnings appear when a product has fewer than 10 keys remaining

## Best Practices
1. Regularly check `/keystats` for low stock warnings
2. Use `/keyhistory` to monitor key usage
3. Keep backups of your key files
4. Test new keys with `/searchkeys` before distributing
5. Monitor `/status` for pending orders

## Troubleshooting
- If commands don't appear, use `/sync` or `!sync`
- If keys aren't being delivered, check the key stock with `/checkkeys`
- If you need to restore keys, use `/restorekeys`
- For any issues with orders, use `/status` to check the current state
