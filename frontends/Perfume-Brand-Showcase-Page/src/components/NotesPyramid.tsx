import { motion } from 'motion/react';
import { ImageWithFallback } from './figma/ImageWithFallback';

interface NotesPyramidProps {
  topNotes: string[];
  middleNotes: string[];
  baseNotes: string[];
}

// Map note names to their images
const noteImages: Record<string, string> = {
  // Top notes - Citrus & Fresh
  'Lemon': 'https://images.unsplash.com/photo-1718196917011-801cddb84334?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxmcmVzaCUyMGxlbW9uJTIwY2l0cnVzfGVufDF8fHx8MTc2MTAzMzgwNHww&ixlib=rb-4.1.0&q=80&w=1080',
  'Bergamot': 'https://images.unsplash.com/photo-1717852885839-166ce0621811?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxiZXJnYW1vdCUyMG9yYW5nZXxlbnwxfHx8fDE3NjEwNjYxMDJ8MA&ixlib=rb-4.1.0&q=80&w=1080',
  'Calabrian Bergamot': 'https://images.unsplash.com/photo-1717852885839-166ce0621811?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxiZXJnYW1vdCUyMG9yYW5nZXxlbnwxfHx8fDE3NjEwNjYxMDJ8MA&ixlib=rb-4.1.0&q=80&w=1080',
  'Grapefruit': 'https://images.unsplash.com/photo-1577234286642-fc512a5f8f11?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxwaW5rJTIwZ3JhcGVmcnVpdHxlbnwxfHx8fDE3NjEwNjYxMDJ8MA&ixlib=rb-4.1.0&q=80&w=1080',
  'Mint': 'https://images.unsplash.com/photo-1648036933917-762235e009c7?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxmcmVzaCUyMG1pbnQlMjBsZWF2ZXN8ZW58MXx8fHwxNzYwOTg1OTU5fDA&ixlib=rb-4.1.0&q=80&w=1080',
  'Pepper': 'https://images.unsplash.com/photo-1649952052743-5e8f37c348c5?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxibGFjayUyMHBlcHBlciUyMHNwaWNlfGVufDF8fHx8MTc2MTA2NjEwMnww&ixlib=rb-4.1.0&q=80&w=1080',
  'Pink Pepper': 'https://images.unsplash.com/photo-1649952052743-5e8f37c348c5?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxibGFjayUyMHBlcHBlciUyMHNwaWNlfGVufDF8fHx8MTc2MTA2NjEwMnww&ixlib=rb-4.1.0&q=80&w=1080',
  'Black Pepper': 'https://images.unsplash.com/photo-1649952052743-5e8f37c348c5?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxibGFjayUyMHBlcHBlciUyMHNwaWNlfGVufDF8fHx8MTc2MTA2NjEwMnww&ixlib=rb-4.1.0&q=80&w=1080',
  'Sichuan Pepper': 'https://images.unsplash.com/photo-1649952052743-5e8f37c348c5?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxibGFjayUyMHBlcHBlciUyMHNwaWNlfGVufDF8fHx8MTc2MTA2NjEwMnww&ixlib=rb-4.1.0&q=80&w=1080',
  'Chinese Pepper': 'https://images.unsplash.com/photo-1649952052743-5e8f37c348c5?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxibGFjayUyMHBlcHBlciUyMHNwaWNlfGVufDF8fHx8MTc2MTA2NjEwMnww&ixlib=rb-4.1.0&q=80&w=1080',
  'Ginger': 'https://images.unsplash.com/photo-1634612828694-8988aa4254df?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxmcmVzaCUyMGdpbmdlciUyMHJvb3R8ZW58MXx8fHwxNzYxMDY2MTAyfDA&ixlib=rb-4.1.0&q=80&w=1080',
  'Raspberry': 'https://images.unsplash.com/photo-1656699331089-0906524c414a?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxyYXNwYmVycnklMjBmcnVpdHxlbnwxfHx8fDE3NjEwNjYxMDN8MA&ixlib=rb-4.1.0&q=80&w=1080',
  'Pineapple': 'https://images.unsplash.com/photo-1632242342964-242876b950c3?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxmcmVzaCUyMHBpbmVhcHBsZXxlbnwxfHx8fDE3NjEwNjYxMDN8MA&ixlib=rb-4.1.0&q=80&w=1080',
  'Apple': 'https://images.unsplash.com/photo-1471943038886-87c772c31367?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxncmVlbiUyMGFwcGxlfGVufDF8fHx8MTc2MTA2NjEwM3ww&ixlib=rb-4.1.0&q=80&w=1080',
  'Orange': 'https://images.unsplash.com/photo-1717852885839-166ce0621811?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxiZXJnYW1vdCUyMG9yYW5nZXxlbnwxfHx8fDE3NjEwNjYxMDJ8MA&ixlib=rb-4.1.0&q=80&w=1080',
  'Mandarin': 'https://images.unsplash.com/photo-1717852885839-166ce0621811?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxiZXJnYW1vdCUyMG9yYW5nZXxlbnwxfHx8fDE3NjEwNjYxMDJ8MA&ixlib=rb-4.1.0&q=80&w=1080',
  'Blackcurrant': 'https://images.unsplash.com/photo-1656699331089-0906524c414a?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxyYXNwYmVycnklMjBmcnVpdHxlbnwxfHx8fDE3NjEwNjYxMDN8MA&ixlib=rb-4.1.0&q=80&w=1080',
  'Incense': 'https://images.unsplash.com/photo-1613750255797-7d4f877615df?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxpbmNlbnNlJTIwc21va2V8ZW58MXx8fHwxNzYwOTU5NDYxfDA&ixlib=rb-4.1.0&q=80&w=1080',
  'Tobacco Leaf': 'https://images.unsplash.com/photo-1669492961902-bf7b0fae83de?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxwYXRjaG91bGklMjBsZWF2ZXN8ZW58MXx8fHwxNzYxMDY2MTA1fDA&ixlib=rb-4.1.0&q=80&w=1080',
  'Spicy Notes': 'https://images.unsplash.com/photo-1649952052743-5e8f37c348c5?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxibGFjayUyMHBlcHBlciUyMHNwaWNlfGVufDF8fHx8MTc2MTA2NjEwMnww&ixlib=rb-4.1.0&q=80&w=1080',
  'Cardamom': 'https://images.unsplash.com/photo-1649952052743-5e8f37c348c5?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxibGFjayUyMHBlcHBlciUyMHNwaWNlfGVufDF8fHx8MTc2MTA2NjEwMnww&ixlib=rb-4.1.0&q=80&w=1080',
  'Sea Notes': 'https://images.unsplash.com/photo-1717852885839-166ce0621811?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxiZXJnYW1vdCUyMG9yYW5nZXxlbnwxfHx8fDE3NjEwNjYxMDJ8MA&ixlib=rb-4.1.0&q=80&w=1080',
  'Aldehydes': 'https://images.unsplash.com/photo-1717852885839-166ce0621811?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxiZXJnYW1vdCUyMG9yYW5nZXxlbnwxfHx8fDE3NjEwNjYxMDJ8MA&ixlib=rb-4.1.0&q=80&w=1080',
  'Rosewood': 'https://images.unsplash.com/photo-1515446134809-993c501ca304?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxjZWRhciUyMHdvb2R8ZW58MXx8fHwxNzYxMDY2MTA2fDA&ixlib=rb-4.1.0&q=80&w=1080',
  
  // Middle notes - Florals & Spices
  'Rose': 'https://images.unsplash.com/photo-1697842609343-0a839fff5d09?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxyZWQlMjByb3NlJTIwZmxvd2VyfGVufDF8fHx8MTc2MTA2NjEwNHww&ixlib=rb-4.1.0&q=80&w=1080',
  'Lavender': 'https://images.unsplash.com/photo-1541927634837-a7d5c4892527?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxsYXZlbmRlciUyMGZsb3dlcnN8ZW58MXx8fHwxNzYxMDE3ODc1fDA&ixlib=rb-4.1.0&q=80&w=1080',
  'Jasmine': 'https://images.unsplash.com/photo-1612380635121-411eda9ecbb9?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxqYXNtaW5lJTIwZmxvd2VyfGVufDF8fHx8MTc2MTA2NjEwNXww&ixlib=rb-4.1.0&q=80&w=1080',
  'Moroccan Jasmine': 'https://images.unsplash.com/photo-1612380635121-411eda9ecbb9?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxqYXNtaW5lJTIwZmxvd2VyfGVufDF8fHx8MTc2MTA2NjEwNXww&ixlib=rb-4.1.0&q=80&w=1080',
  'Iris': 'https://images.unsplash.com/photo-1672665908489-9c42379ebb3d?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxpcmlzJTIwZmxvd2VyfGVufDF8fHx8MTc2MTA0MDAzM3ww&ixlib=rb-4.1.0&q=80&w=1080',
  'Patchouli': 'https://images.unsplash.com/photo-1669492961902-bf7b0fae83de?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxwYXRjaG91bGklMjBsZWF2ZXN8ZW58MXx8fHwxNzYxMDY2MTA1fDA&ixlib=rb-4.1.0&q=80&w=1080',
  'Cocoa': 'https://images.unsplash.com/photo-1507576164121-220762647800?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxjb2NvYSUyMGJlYW5zfGVufDF8fHx8MTc2MTA0NTI1M3ww&ixlib=rb-4.1.0&q=80&w=1080',
  'Neroli': 'https://images.unsplash.com/photo-1612380635121-411eda9ecbb9?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxqYXNtaW5lJTIwZmxvd2VyfGVufDF8fHx8MTc2MTA2NjEwNXww&ixlib=rb-4.1.0&q=80&w=1080',
  'Orange Blossom': 'https://images.unsplash.com/photo-1612380635121-411eda9ecbb9?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxqYXNtaW5lJTIwZmxvd2VyfGVufDF8fHx8MTc2MTA2NjEwNXww&ixlib=rb-4.1.0&q=80&w=1080',
  'Black Tea': 'https://images.unsplash.com/photo-1669492961902-bf7b0fae83de?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxwYXRjaG91bGklMjBsZWF2ZXN8ZW58MXx8fHwxNzYxMDY2MTA1fDA&ixlib=rb-4.1.0&q=80&w=1080',
  'Pear': 'https://images.unsplash.com/photo-1471943038886-87c772c31367?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxncmVlbiUyMGFwcGxlfGVufDF8fHx8MTc2MTA2NjEwM3ww&ixlib=rb-4.1.0&q=80&w=1080',
  'Geranium': 'https://images.unsplash.com/photo-1697842609343-0a839fff5d09?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxyZWQlMjByb3NlJTIwZmxvd2VyfGVufDF8fHx8MTc2MTA2NjEwNHww&ixlib=rb-4.1.0&q=80&w=1080',
  'Saffron': 'https://images.unsplash.com/photo-1649952052743-5e8f37c348c5?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxibGFjayUyMHBlcHBlciUyMHNwaWNlfGVufDF8fHx8MTc2MTA2NjEwMnww&ixlib=rb-4.1.0&q=80&w=1080',
  'Nutmeg': 'https://images.unsplash.com/photo-1649952052743-5e8f37c348c5?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxibGFjayUyMHBlcHBlciUyMHNwaWNlfGVufDF8fHx8MTc2MTA2NjEwMnww&ixlib=rb-4.1.0&q=80&w=1080',
  'Iso E Super': 'https://images.unsplash.com/photo-1515446134809-993c501ca304?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxjZWRhciUyMHdvb2R8ZW58MXx8fHwxNzYxMDY2MTA2fDA&ixlib=rb-4.1.0&q=80&w=1080',
  'Birch': 'https://images.unsplash.com/photo-1515446134809-993c501ca304?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxjZWRhciUyMHdvb2R8ZW58MXx8fHwxNzYxMDY2MTA2fDA&ixlib=rb-4.1.0&q=80&w=1080',
  'Virginia Cedar': 'https://images.unsplash.com/photo-1515446134809-993c501ca304?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxjZWRhciUyMHdvb2R8ZW58MXx8fHwxNzYxMDY2MTA2fDA&ixlib=rb-4.1.0&q=80&w=1080',
  
  // Base notes - Woods & Resins
  'Sandalwood': 'https://images.unsplash.com/photo-1616662707741-9f32deea4863?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxzYW5kYWx3b29kJTIwY2hpcHN8ZW58MXx8fHwxNzYxMDY2MTA2fDA&ixlib=rb-4.1.0&q=80&w=1080',
  'Cedar': 'https://images.unsplash.com/photo-1515446134809-993c501ca304?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxjZWRhciUyMHdvb2R8ZW58MXx8fHwxNzYxMDY2MTA2fDA&ixlib=rb-4.1.0&q=80&w=1080',
  'Vanilla': 'https://images.unsplash.com/photo-1682482198446-4cbf92f85a4b?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2YW5pbGxhJTIwYmVhbnN8ZW58MXx8fHwxNzYxMDY2MTA3fDA&ixlib=rb-4.1.0&q=80&w=1080',
  'Tonka Bean': 'https://images.unsplash.com/photo-1585240698295-e14d61c50625?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx0b25rYSUyMGJlYW5zfGVufDF8fHx8MTc2MTA2NjEwN3ww&ixlib=rb-4.1.0&q=80&w=1080',
  'Amber': 'https://images.unsplash.com/photo-1740819912820-6535ad66884a?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxhbWJlciUyMHJlc2lufGVufDF8fHx8MTc2MTA2NjEwOHww&ixlib=rb-4.1.0&q=80&w=1080',
  'Vetiver': 'https://images.unsplash.com/photo-1682637520012-60230eddde9e?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2ZXRpdmVyJTIwZ3Jhc3N8ZW58MXx8fHwxNzYxMDY2MTA4fDA&ixlib=rb-4.1.0&q=80&w=1080',
  'Oud Wood': 'https://images.unsplash.com/photo-1684039568465-24c31d0cc80f?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxvdWQlMjB3b29kfGVufDF8fHx8MTc2MTA2NjEwOHww&ixlib=rb-4.1.0&q=80&w=1080',
  'Musk': 'https://images.unsplash.com/photo-1717852885839-166ce0621811?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxtdXNrJTIwcGVyZnVtZXxlbnwxfHx8fDE3NjEwNjYxMDh8MA&ixlib=rb-4.1.0&q=80&w=1080',
  'White Musk': 'https://images.unsplash.com/photo-1717852885839-166ce0621811?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxtdXNrJTIwcGVyZnVtZXxlbnwxfHx8fDE3NjEwNjYxMDh8MA&ixlib=rb-4.1.0&q=80&w=1080',
  'Benzoin': 'https://images.unsplash.com/photo-1740819912820-6535ad66884a?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxhbWJlciUyMHJlc2lufGVufDF8fHx8MTc2MTA2NjEwOHww&ixlib=rb-4.1.0&q=80&w=1080',
  'Ambroxan': 'https://images.unsplash.com/photo-1740819912820-6535ad66884a?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxhbWJlciUyMHJlc2lufGVufDF8fHx8MTc2MTA2NjEwOHww&ixlib=rb-4.1.0&q=80&w=1080',
  'Ambergris': 'https://images.unsplash.com/photo-1740819912820-6535ad66884a?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxhbWJlciUyMHJlc2lufGVufDF8fHx8MTc2MTA2NjEwOHww&ixlib=rb-4.1.0&q=80&w=1080',
  'Labdanum': 'https://images.unsplash.com/photo-1740819912820-6535ad66884a?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxhbWJlciUyMHJlc2lufGVufDF8fHx8MTc2MTA2NjEwOHww&ixlib=rb-4.1.0&q=80&w=1080',
  'Oak Moss': 'https://images.unsplash.com/photo-1682637520012-60230eddde9e?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2ZXRpdmVyJTIwZ3Jhc3N8ZW58MXx8fHwxNzYxMDY2MTA4fDA&ixlib=rb-4.1.0&q=80&w=1080',
  'Leather': 'https://images.unsplash.com/photo-1515446134809-993c501ca304?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxjZWRhciUyMHdvb2R8ZW58MXx8fHwxNzYxMDY2MTA2fDA&ixlib=rb-4.1.0&q=80&w=1080',
  'Dried Fruits': 'https://images.unsplash.com/photo-1585240698295-e14d61c50625?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx0b25rYSUyMGJlYW5zfGVufDF8fHx8MTc2MTA2NjEwN3ww&ixlib=rb-4.1.0&q=80&w=1080',
  'Woody Notes': 'https://images.unsplash.com/photo-1515446134809-993c501ca304?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxjZWRhciUyMHdvb2R8ZW58MXx8fHwxNzYxMDY2MTA2fDA&ixlib=rb-4.1.0&q=80&w=1080',
  'Elemi': 'https://images.unsplash.com/photo-1740819912820-6535ad66884a?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxhbWJlciUyMHJlc2lufGVufDF8fHx8MTc2MTA2NjEwOHww&ixlib=rb-4.1.0&q=80&w=1080',
};

// Get image for a note, or return null
const getNoteImage = (note: string): string | null => {
  return noteImages[note] || null;
};

export function NotesPyramid({ topNotes, middleNotes, baseNotes }: NotesPyramidProps) {
  // Get up to 3 images for each tier
  const topNotesData = topNotes.slice(0, 3).map(note => ({
    name: note,
    image: getNoteImage(note)
  })).filter(item => item.image);

  const middleNotesData = middleNotes.slice(0, 3).map(note => ({
    name: note,
    image: getNoteImage(note)
  })).filter(item => item.image);

  const baseNotesData = baseNotes.slice(0, 4).map(note => ({
    name: note,
    image: getNoteImage(note)
  })).filter(item => item.image);

  return (
    <div className="relative w-full max-w-4xl mx-auto py-16">
      {/* Title */}
      <motion.div
        className="text-center mb-12"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
      >
        <h3 className="text-3xl tracking-[0.3em] text-transparent bg-clip-text bg-gradient-to-r from-amber-400 via-teal-400 to-emerald-400 mb-2">
          OLFACTORY PYRAMID
        </h3>
        <div className="w-32 h-[1px] bg-gradient-to-r from-transparent via-teal-500 to-transparent mx-auto"></div>
      </motion.div>

      {/* Pyramid Container */}
      <div className="relative">
        {/* Background glow effect */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-96 h-96 bg-gradient-radial from-amber-500/10 via-teal-500/5 to-transparent rounded-full blur-3xl"></div>
        </div>

        {/* SVG Pyramid Structure */}
        <svg viewBox="0 0 800 700" className="w-full h-auto relative z-0">
          <defs>
            {/* Enhanced glow filters */}
            <filter id="strongGlow">
              <feGaussianBlur stdDeviation="8" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
            
            <filter id="innerGlow">
              <feGaussianBlur stdDeviation="4" result="blur"/>
              <feComposite in="blur" in2="SourceGraphic" operator="out"/>
              <feFlood floodColor="#ffffff" floodOpacity="0.3" result="color"/>
              <feComposite in="color" in2="SourceAlpha" operator="in" result="innerGlow"/>
              <feMerge>
                <feMergeNode in="innerGlow"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>

            {/* Gradients with more depth */}
            <linearGradient id="topGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" style={{ stopColor: '#fbbf24', stopOpacity: 0.25 }} />
              <stop offset="50%" style={{ stopColor: '#f59e0b', stopOpacity: 0.15 }} />
              <stop offset="100%" style={{ stopColor: '#d97706', stopOpacity: 0.1 }} />
            </linearGradient>
            
            <linearGradient id="middleGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" style={{ stopColor: '#14b8a6', stopOpacity: 0.25 }} />
              <stop offset="50%" style={{ stopColor: '#0d9488', stopOpacity: 0.15 }} />
              <stop offset="100%" style={{ stopColor: '#0f766e', stopOpacity: 0.1 }} />
            </linearGradient>
            
            <linearGradient id="baseGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" style={{ stopColor: '#10b981', stopOpacity: 0.25 }} />
              <stop offset="50%" style={{ stopColor: '#059669', stopOpacity: 0.15 }} />
              <stop offset="100%" style={{ stopColor: '#047857', stopOpacity: 0.1 }} />
            </linearGradient>

            {/* Radial gradients for depth */}
            <radialGradient id="topRadial" cx="50%" cy="30%">
              <stop offset="0%" style={{ stopColor: '#fbbf24', stopOpacity: 0.4 }} />
              <stop offset="100%" style={{ stopColor: '#f59e0b', stopOpacity: 0.1 }} />
            </radialGradient>
            <radialGradient id="middleRadial" cx="50%" cy="50%">
              <stop offset="0%" style={{ stopColor: '#14b8a6', stopOpacity: 0.4 }} />
              <stop offset="100%" style={{ stopColor: '#0d9488', stopOpacity: 0.1 }} />
            </radialGradient>
            <radialGradient id="baseRadial" cx="50%" cy="70%">
              <stop offset="0%" style={{ stopColor: '#10b981', stopOpacity: 0.4 }} />
              <stop offset="100%" style={{ stopColor: '#059669', stopOpacity: 0.1 }} />
            </radialGradient>
          </defs>
          
          {/* Ambient glow circles */}
          <circle cx="400" cy="350" r="320" fill="none" stroke="url(#topGradient)" strokeWidth="0.5" opacity="0.15" />
          <circle cx="400" cy="350" r="280" fill="none" stroke="url(#middleGradient)" strokeWidth="0.5" opacity="0.15" />
          
          {/* Top Section - Triangle */}
          <motion.path
            d="M 400 100 L 580 280 L 220 280 Z"
            fill="url(#topRadial)"
            stroke="#fbbf24"
            strokeWidth="3"
            filter="url(#strongGlow)"
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 1, ease: "easeOut" }}
          />
          
          {/* Middle Section - Trapezoid */}
          <motion.path
            d="M 220 280 L 580 280 L 620 430 L 180 430 Z"
            fill="url(#middleRadial)"
            stroke="#14b8a6"
            strokeWidth="3"
            filter="url(#strongGlow)"
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 1, delay: 0.2, ease: "easeOut" }}
          />
          
          {/* Base Section - Wider Trapezoid */}
          <motion.path
            d="M 180 430 L 620 430 L 660 580 L 140 580 Z"
            fill="url(#baseRadial)"
            stroke="#10b981"
            strokeWidth="3"
            filter="url(#strongGlow)"
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 1, delay: 0.4, ease: "easeOut" }}
          />
          
          {/* Decorative corner accents with glow */}
          <motion.g initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.8, type: "spring" }}>
            <circle cx="400" cy="100" r="8" fill="#fbbf24" filter="url(#strongGlow)" />
            <circle cx="400" cy="100" r="4" fill="#fff" opacity="0.8" />
          </motion.g>
          <motion.g initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.9, type: "spring" }}>
            <circle cx="140" cy="580" r="8" fill="#10b981" filter="url(#strongGlow)" />
            <circle cx="140" cy="580" r="4" fill="#fff" opacity="0.8" />
          </motion.g>
          <motion.g initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.9, type: "spring" }}>
            <circle cx="660" cy="580" r="8" fill="#10b981" filter="url(#strongGlow)" />
            <circle cx="660" cy="580" r="4" fill="#fff" opacity="0.8" />
          </motion.g>

          {/* Divider lines */}
          <motion.line
            x1="220" y1="280" x2="580" y2="280"
            stroke="#fff"
            strokeWidth="1"
            opacity="0.2"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 0.8, delay: 0.6 }}
          />
          <motion.line
            x1="180" y1="430" x2="620" y2="430"
            stroke="#fff"
            strokeWidth="1"
            opacity="0.2"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 0.8, delay: 0.8 }}
          />
        </svg>

        {/* Content Overlay */}
        <div className="absolute inset-0 flex flex-col justify-between py-12 px-8">
          {/* TOP NOTES */}
          <div className="flex flex-col items-center pt-8">
            <motion.div
              className="text-amber-400 tracking-[0.3em] text-sm mb-6"
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.7 }}
            >
              TOP NOTES
            </motion.div>
            {topNotesData.length > 0 && (
              <div className="flex justify-center items-end gap-4">
                {topNotesData.map((note, idx) => (
                  <motion.div
                    key={idx}
                    className="flex flex-col items-center"
                    initial={{ opacity: 0, y: 20, scale: 0.8 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    transition={{ duration: 0.6, delay: 0.8 + idx * 0.1 }}
                  >
                    <div className="relative group">
                      <div className="absolute inset-0 bg-amber-400/30 rounded-full blur-xl group-hover:blur-2xl transition-all duration-500"></div>
                      <div 
                        className="relative rounded-full overflow-hidden border-2 border-amber-400/50 shadow-2xl shadow-amber-500/30"
                        style={{ 
                          width: topNotesData.length === 1 ? '100px' : topNotesData.length === 2 ? '80px' : '70px',
                          height: topNotesData.length === 1 ? '100px' : topNotesData.length === 2 ? '80px' : '70px',
                        }}
                      >
                        <ImageWithFallback
                          src={note.image!}
                          alt={note.name}
                          className="w-full h-full object-cover transform group-hover:scale-110 transition-transform duration-500"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent"></div>
                      </div>
                    </div>
                    <div className="mt-3 text-xs text-amber-200/90 text-center max-w-[80px] leading-tight">
                      {note.name}
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </div>

          {/* HEART NOTES */}
          <div className="flex flex-col items-center">
            <motion.div
              className="text-teal-400 tracking-[0.3em] text-sm mb-6"
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 1.0 }}
            >
              HEART NOTES
            </motion.div>
            {middleNotesData.length > 0 && (
              <div className="flex justify-center items-end gap-4">
                {middleNotesData.map((note, idx) => (
                  <motion.div
                    key={idx}
                    className="flex flex-col items-center"
                    initial={{ opacity: 0, y: 20, scale: 0.8 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    transition={{ duration: 0.6, delay: 1.1 + idx * 0.1 }}
                  >
                    <div className="relative group">
                      <div className="absolute inset-0 bg-teal-400/30 rounded-full blur-xl group-hover:blur-2xl transition-all duration-500"></div>
                      <div 
                        className="relative rounded-full overflow-hidden border-2 border-teal-400/50 shadow-2xl shadow-teal-500/30"
                        style={{ 
                          width: middleNotesData.length === 1 ? '110px' : middleNotesData.length === 2 ? '90px' : '75px',
                          height: middleNotesData.length === 1 ? '110px' : middleNotesData.length === 2 ? '90px' : '75px',
                        }}
                      >
                        <ImageWithFallback
                          src={note.image!}
                          alt={note.name}
                          className="w-full h-full object-cover transform group-hover:scale-110 transition-transform duration-500"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent"></div>
                      </div>
                    </div>
                    <div className="mt-3 text-xs text-teal-200/90 text-center max-w-[90px] leading-tight">
                      {note.name}
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </div>

          {/* BASE NOTES */}
          <div className="flex flex-col items-center pb-4">
            <motion.div
              className="text-emerald-400 tracking-[0.3em] text-sm mb-6"
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 1.3 }}
            >
              BASE NOTES
            </motion.div>
            {baseNotesData.length > 0 && (
              <div className="flex justify-center items-end gap-5">
                {baseNotesData.map((note, idx) => (
                  <motion.div
                    key={idx}
                    className="flex flex-col items-center"
                    initial={{ opacity: 0, y: 20, scale: 0.8 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    transition={{ duration: 0.6, delay: 1.4 + idx * 0.1 }}
                  >
                    <div className="relative group">
                      <div className="absolute inset-0 bg-emerald-400/30 rounded-full blur-xl group-hover:blur-2xl transition-all duration-500"></div>
                      <div 
                        className="relative rounded-full overflow-hidden border-2 border-emerald-400/50 shadow-2xl shadow-emerald-500/30"
                        style={{ 
                          width: baseNotesData.length === 1 ? '120px' : baseNotesData.length === 2 ? '100px' : baseNotesData.length === 3 ? '80px' : '70px',
                          height: baseNotesData.length === 1 ? '120px' : baseNotesData.length === 2 ? '100px' : baseNotesData.length === 3 ? '80px' : '70px',
                        }}
                      >
                        <ImageWithFallback
                          src={note.image!}
                          alt={note.name}
                          className="w-full h-full object-cover transform group-hover:scale-110 transition-transform duration-500"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent"></div>
                      </div>
                    </div>
                    <div className="mt-3 text-xs text-emerald-200/90 text-center max-w-[90px] leading-tight">
                      {note.name}
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
