class BeerSynonymExpander:
    def __init__(self):
        self.synonyms = {
            # Стили пива
            "ipa": ["индийский пейл-эль", "ипа", "india pale ale"],
            "neipa": ["нью инглэнд айпиэй", "мутный ipa", "сочный ipa"],
            "stout": ["стаут", "имперский стаут", "сухой стаут"],
            "sour": ["кислое", "сорное", "wild ale", "кислый эль", "сауэр"],
            "cider": ["cidr", "сидр", "яблочный сидр"],
            "punk":["панк", "punk ipa", "панкипа"],
            
            # Характеристики
            "горьк": ["горечь", "bitterness", "горький вкус", "горчинка"],
            "аромат": ["букет", "нос", "ароматика", "запах", "пахнет"],
            "тело": ["плотность", "насыщенность", "mouthfeel"],
            
            # Процессы
            "фермент": ["брожение", "созревание", "выдержка"],
            "хмелев": ["хмеледобавление", "дрихоп", "холодное охмеление"],

            # бренды
            "saldens": ["салденс"]
        }
        
        # Обратный индекс для быстрого поиска
        self.reverse_index = {}
        for key, values in self.synonyms.items():
            for value in values:
                self.reverse_index[value] = key
    
    def expand_text(self, text):
        """Основная функция расширения"""
        words = text.lower().split()
        expanded = []
        
        for word in words:
            # Добавляем оригинальное слово
            expanded.append(word)
            
            # Ищем синонимы
            # 1. Прямое совпадение
            if word in self.synonyms:
                expanded.extend(self.synonyms[word])
            
            # 2. Частичное совпадение
            for key in self.synonyms:
                if key in word and len(key) > 3:
                    expanded.extend(self.synonyms[key])
        
        # Удаляем дубликаты, сохраняя порядок
        seen = set()
        result = []
        for word in expanded:
            if word not in seen:
                seen.add(word)
                result.append(word)
        
        return " ".join(result)

# Использование
#expander = BeerSynonymExpander()
#query = "сухой стаут с кофейными нотами"
#enhanced = expander.expand_text(query)
# Результат: "сухой стаут стаут имперский стаут сухой стаут с кофейными нотами"