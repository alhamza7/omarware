import { Brand } from '../types/perfume';

export const brandsData: Brand[] = [
  {
    id: 'louis-vuitton',
    name: 'Louis Vuitton',
    country: 'France',
    perfumes: [
      {
        id: 'lv-1',
        name: 'Ombre Nomade',
        brand: 'Louis Vuitton',
        image: 'https://images.unsplash.com/photo-1719175936556-dbd05e415913?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxsdXh1cnklMjBwZXJmdW1lJTIwYm90dGxlfGVufDF8fHx8MTc2MDk4MTM1M3ww&ixlib=rb-4.1.0&q=80&w=1080',
        season: ['Fall', 'Winter'],
        occasion: ['Evening', 'Special Events'],
        longevity: '8-10 hours',
        sillage: 'Heavy',
        description: 'A mystical and woody fragrance inspired by the endless desert. Rich oud and incense create a powerful and sophisticated scent.',
        notes: {
          top: ['Incense', 'Raspberry'],
          middle: ['Rose', 'Saffron', 'Geranium'],
          base: ['Oud Wood', 'Birch', 'Benzoin']
        }
      },
      {
        id: 'lv-2',
        name: 'Imagination',
        brand: 'Louis Vuitton',
        image: 'https://images.unsplash.com/photo-1759793500112-c588839cfc6e?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxlbGVnYW50JTIwZnJhZ3JhbmNlJTIwYm90dGxlfGVufDF8fHx8MTc2MDk5NTc5OXww&ixlib=rb-4.1.0&q=80&w=1080',
        season: ['Spring', 'Summer'],
        occasion: ['Daytime', 'Office'],
        longevity: '6-8 hours',
        sillage: 'Moderate',
        description: 'A citrus aromatic scent that captures the essence of boundless imagination with fresh and vibrant notes.',
        notes: {
          top: ['Bergamot', 'Mandarin', 'Ginger'],
          middle: ['Black Tea', 'Neroli'],
          base: ['Ambroxan', 'Musk', 'Cedar']
        }
      },
      {
        id: 'lv-3',
        name: 'Afternoon Swim',
        brand: 'Louis Vuitton',
        image: 'https://images.unsplash.com/photo-1624798956425-ef88fc12b540?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxkZXNpZ25lciUyMHBlcmZ1bWV8ZW58MXx8fHwxNzYxMDE1MTYyfDA&ixlib=rb-4.1.0&q=80&w=1080',
        season: ['Spring', 'Summer'],
        occasion: ['Casual', 'Vacation'],
        longevity: '5-7 hours',
        sillage: 'Light',
        description: 'A fresh aquatic fragrance reminiscent of a refreshing swim on a sunny afternoon.',
        notes: {
          top: ['Orange', 'Mandarin'],
          middle: ['Orange Blossom', 'Iris'],
          base: ['Musk', 'Vetiver']
        }
      }
    ]
  },
  {
    id: 'dior',
    name: 'Dior',
    country: 'France',
    perfumes: [
      {
        id: 'dior-1',
        name: 'Sauvage',
        brand: 'Dior',
        image: 'https://images.unsplash.com/photo-1758871992965-836e1fb0f9bc?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxwcmVtaXVtJTIwY29sb2duZSUyMGJvdHRsZXxlbnwxfHx8fDE3NjEwMjQyNjh8MA&ixlib=rb-4.1.0&q=80&w=1080',
        season: ['All Seasons'],
        occasion: ['Daytime', 'Evening', 'Office'],
        longevity: '7-9 hours',
        sillage: 'Strong',
        description: 'A radically fresh composition inspired by wide-open spaces. Raw and noble ingredients create a powerful and refined scent.',
        notes: {
          top: ['Calabrian Bergamot', 'Pepper'],
          middle: ['Sichuan Pepper', 'Lavender', 'Pink Pepper', 'Vetiver', 'Patchouli', 'Geranium'],
          base: ['Ambroxan', 'Cedar', 'Labdanum']
        }
      },
      {
        id: 'dior-2',
        name: 'Homme Intense',
        brand: 'Dior',
        image: 'https://images.unsplash.com/photo-1673442598728-71caf1f15820?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxwZXJmdW1lJTIwY29sbGVjdGlvbiUyMGRpc3BsYXl8ZW58MXx8fHwxNzYxMDI0MjY5fDA&ixlib=rb-4.1.0&q=80&w=1080',
        season: ['Fall', 'Winter'],
        occasion: ['Evening', 'Romantic'],
        longevity: '6-8 hours',
        sillage: 'Moderate',
        description: 'An intense woody fragrance with iris and precious wood notes for a sophisticated masculine appeal.',
        notes: {
          top: ['Lavender', 'Bergamot'],
          middle: ['Iris', 'Pear', 'Virginia Cedar'],
          base: ['Vetiver', 'Leather']
        }
      }
    ]
  },
  {
    id: 'chanel',
    name: 'Chanel',
    country: 'France',
    perfumes: [
      {
        id: 'chanel-1',
        name: 'Bleu de Chanel',
        brand: 'Chanel',
        image: 'https://images.unsplash.com/photo-1719175936556-dbd05e415913?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxsdXh1cnklMjBwZXJmdW1lJTIwYm90dGxlfGVufDF8fHx8MTc2MDk4MTM1M3ww&ixlib=rb-4.1.0&q=80&w=1080',
        season: ['All Seasons'],
        occasion: ['Office', 'Daytime', 'Evening'],
        longevity: '7-9 hours',
        sillage: 'Strong',
        description: 'An aromatic-woody fragrance that embodies freedom with a captivating blend of citrus and woods.',
        notes: {
          top: ['Grapefruit', 'Lemon', 'Mint', 'Pink Pepper'],
          middle: ['Ginger', 'Jasmine', 'Iso E Super', 'Nutmeg'],
          base: ['Incense', 'Vetiver', 'Cedar', 'Sandalwood', 'Patchouli']
        }
      },
      {
        id: 'chanel-2',
        name: 'Allure Homme Sport',
        brand: 'Chanel',
        image: 'https://images.unsplash.com/photo-1759793500112-c588839cfc6e?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxlbGVnYW50JTIwZnJhZ3JhbmNlJTIwYm90dGxlfGVufDF8fHx8MTc2MDk5NTc5OXww&ixlib=rb-4.1.0&q=80&w=1080',
        season: ['Spring', 'Summer'],
        occasion: ['Sport', 'Casual', 'Daytime'],
        longevity: '5-7 hours',
        sillage: 'Moderate',
        description: 'A fresh and energizing fragrance perfect for the active man. Clean and invigorating notes.',
        notes: {
          top: ['Mandarin', 'Sea Notes', 'Aldehydes'],
          middle: ['Neroli', 'Cedar', 'Black Pepper'],
          base: ['Tonka Bean', 'Vanilla', 'White Musk', 'Vetiver', 'Elemi']
        }
      }
    ]
  },
  {
    id: 'tom-ford',
    name: 'Tom Ford',
    country: 'USA',
    perfumes: [
      {
        id: 'tf-1',
        name: 'Oud Wood',
        brand: 'Tom Ford',
        image: 'https://images.unsplash.com/photo-1624798956425-ef88fc12b540?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxkZXNpZ25lciUyMHBlcmZ1bWV8ZW58MXx8fHwxNzYxMDE1MTYyfDA&ixlib=rb-4.1.0&q=80&w=1080',
        season: ['Fall', 'Winter'],
        occasion: ['Evening', 'Special Events'],
        longevity: '8-10 hours',
        sillage: 'Heavy',
        description: 'Rare oud wood combined with exotic spices and sensual amber creates an intensely luxurious fragrance.',
        notes: {
          top: ['Rosewood', 'Cardamom', 'Chinese Pepper'],
          middle: ['Oud Wood', 'Sandalwood', 'Vetiver'],
          base: ['Tonka Bean', 'Vanilla', 'Amber']
        }
      },
      {
        id: 'tf-2',
        name: 'Tobacco Vanille',
        brand: 'Tom Ford',
        image: 'https://images.unsplash.com/photo-1758871992965-836e1fb0f9bc?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxwcmVtaXVtJTIwY29sb2duZSUyMGJvdHRsZXxlbnwxfHx8fDE3NjEwMjQyNjh8MA&ixlib=rb-4.1.0&q=80&w=1080',
        season: ['Fall', 'Winter'],
        occasion: ['Evening', 'Romantic'],
        longevity: '9-12 hours',
        sillage: 'Very Heavy',
        description: 'An opulent and oriental fragrance with creamy tonka bean, vanilla, and sweet tobacco leaf.',
        notes: {
          top: ['Tobacco Leaf', 'Spicy Notes'],
          middle: ['Vanilla', 'Cocoa', 'Tonka Bean'],
          base: ['Dried Fruits', 'Woody Notes']
        }
      }
    ]
  },
  {
    id: 'creed',
    name: 'Creed',
    country: 'France',
    perfumes: [
      {
        id: 'creed-1',
        name: 'Aventus',
        brand: 'Creed',
        image: 'https://images.unsplash.com/photo-1673442598728-71caf1f15820?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxwZXJmdW1lJTIwY29sbGVjdGlvbiUyMGRpc3BsYXl8ZW58MXx8fHwxNzYxMDI0MjY5fDA&ixlib=rb-4.1.0&q=80&w=1080',
        season: ['All Seasons'],
        occasion: ['Office', 'Daytime', 'Evening'],
        longevity: '8-10 hours',
        sillage: 'Strong',
        description: 'A legendary fragrance celebrating strength, vision and success. Fresh and fruity with a smoky base.',
        notes: {
          top: ['Pineapple', 'Blackcurrant', 'Apple', 'Bergamot'],
          middle: ['Birch', 'Patchouli', 'Moroccan Jasmine', 'Rose'],
          base: ['Musk', 'Oak Moss', 'Ambergris', 'Vanilla']
        }
      }
    ]
  }
];
