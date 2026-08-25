"""
Transcript generation service
"""

import discord
import aiofiles
import os
import html
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class TranscriptService:
    """Transcript service for generating ticket transcripts"""
    
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.transcript_dir = Path("transcripts")
        self.transcript_dir.mkdir(exist_ok=True)
    
    async def generate_transcript(
        self,
        channel: discord.TextChannel,
        ticket_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        Generate transcript for a ticket channel
        Returns file path or None if failed
        """
        try:
            # Fetch all messages
            messages = []
            async for message in channel.history(limit=None, oldest_first=True):
                messages.append(message)
            
            # Generate HTML content
            html_content = await self._generate_html(channel, ticket_data, messages)
            
            # Save transcript
            filename = f"{ticket_data['ticket_id']}.html"
            filepath = self.transcript_dir / filename
            
            async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                await f.write(html_content)
            
            logger.info(f"Transcript saved: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to generate transcript for {ticket_data['ticket_id']}: {e}", exc_info=True)
            return None
    
    async def _generate_html(
        self,
        channel: discord.TextChannel,
        ticket_data: Dict[str, Any],
        messages: List[discord.Message]
    ) -> str:
        """Generate HTML transcript"""
        
        # Escape helper
        def escape(text: str) -> str:
            return html.escape(str(text), quote=True)
        
        # Build messages HTML
        messages_html = []
        for message in messages:
            author_name = escape(f"{message.author.name}#{message.author.discriminator}")
            timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
            
            # Format content
            content = escape(message.content) if message.content else ""
            
            # Add attachments
            attachments_html = []
            for attachment in message.attachments:
                attachments_html.append(
                    f'<div class="attachment">'
                    f'<a href="{escape(attachment.url)}" target="_blank">📎 {escape(attachment.filename)}</a>'
                    f'</div>'
                )
            
            # Add embeds
            embeds_html = []
            for embed in message.embeds:
                embed_html = '<div class="embed">'
                if embed.title:
                    embed_html += f'<div class="embed-title">{escape(embed.title)}</div>'
                if embed.description:
                    embed_html += f'<div class="embed-description">{escape(embed.description)}</div>'
                for field in embed.fields:
                    embed_html += f'<div class="embed-field"><strong>{escape(field.name)}:</strong> {escape(field.value)}</div>'
                embed_html += '</div>'
                embeds_html.append(embed_html)
            
            message_html = f'''
            <div class="message">
                <div class="message-header">
                    <img src="{message.author.avatar.url if message.author.avatar else 'https://cdn.discordapp.com/embed/avatars/0.png'}" 
                         class="avatar" alt="Avatar" onerror="this.src='https://cdn.discordapp.com/embed/avatars/0.png'">
                    <span class="author">{author_name}</span>
                    <span class="timestamp">{timestamp}</span>
                </div>
                <div class="message-content">{content}</div>
                {''.join(attachments_html)}
                {''.join(embeds_html)}
            </div>
            '''
            messages_html.append(message_html)
        
        # Build full HTML
        created_at = datetime.fromisoformat(ticket_data['created_at']).strftime("%Y-%m-%d %H:%M:%S")
        closed_at = datetime.fromisoformat(ticket_data['closed_at']).strftime("%Y-%m-%d %H:%M:%S") if ticket_data.get('closed_at') else "N/A"
        
        full_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Transcript - {escape(ticket_data['ticket_id'])}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: #5865F2;
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .header h1 {{
            font-size: 28px;
            margin-bottom: 10px;
        }}
        .header-info {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
            margin-top: 15px;
        }}
        .info-item {{
            font-size: 14px;
        }}
        .info-item strong {{
            display: block;
            font-size: 12px;
            text-transform: uppercase;
            opacity: 0.8;
        }}
        .messages {{
            background: white;
            border-radius: 10px;
            padding: 20px;
        }}
        .message {{
            margin-bottom: 15px;
            padding: 15px;
            background: #f9f9f9;
            border-radius: 8px;
            border-left: 4px solid #5865F2;
        }}
        .message-header {{
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }}
        .avatar {{
            width: 40px;
            height: 40px;
            border-radius: 50%;
            margin-right: 10px;
        }}
        .author {{
            font-weight: bold;
            margin-right: 10px;
        }}
        .timestamp {{
            font-size: 12px;
            color: #666;
        }}
        .message-content {{
            margin-left: 50px;
            word-wrap: break-word;
        }}
        .attachment {{
            margin-left: 50px;
            margin-top: 10px;
            padding: 10px;
            background: #e8e8e8;
            border-radius: 5px;
        }}
        .attachment a {{
            color: #5865F2;
            text-decoration: none;
        }}
        .embed {{
            margin-left: 50px;
            margin-top: 10px;
            padding: 10px;
            background: #f0f0f0;
            border-radius: 5px;
            border-left: 4px solid #4CAF50;
        }}
        .embed-title {{
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .embed-description {{
            margin-bottom: 5px;
        }}
        .embed-field {{
            margin: 5px 0;
            font-size: 14px;
        }}
        .footer {{
            text-align: center;
            margin-top: 20px;
            padding: 20px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Ticket Transcript</h1>
            <div class="header-info">
                <div class="info-item">
                    <strong>Ticket ID</strong>
                    {escape(ticket_data['ticket_id'])}
                </div>
                <div class="info-item">
                    <strong>Channel</strong>
                    #{escape(channel.name)}
                </div>
                <div class="info-item">
                    <strong>User ID</strong>
                    {escape(ticket_data['user_id'])}
                </div>
                <div class="info-item">
                    <strong>Type</strong>
                    {escape(ticket_data['ticket_type'])}
                </div>
                <div class="info-item">
                    <strong>Opened</strong>
                    {created_at}
                </div>
                <div class="info-item">
                    <strong>Closed</strong>
                    {closed_at}
                </div>
            </div>
        </div>
        <div class="messages">
            {''.join(messages_html) if messages_html else '<p style="text-align:center;color:#666;">No messages in this ticket.</p>'}
        </div>
        <div class="footer">
            Generated by Discord Ticket Bot • {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}
        </div>
    </div>
</body>
</html>'''
        
        return full_html
    
    def delete_transcript(self, filepath: str) -> None:
        """Delete transcript file"""
        try:
            if filepath and os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"Transcript deleted: {filepath}")
        except Exception as e:
            logger.error(f"Failed to delete transcript {filepath}: {e}")
