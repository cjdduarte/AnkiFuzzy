
## Configuração do AnkiFuzzy / AnkiFuzzy Configuration

### FIELDS_TO_CHECK

#### Português (pt-BR)

**Descrição**: Lista de campos que o AnkiFuzzy verifica para encontrar o conteúdo dos cartões. Esses campos são usados para extrair o texto de cada cartão e realizar comparações de similaridade.

**Exemplo**: 
```
"FIELDS_TO_CHECK": ["Frente", "Front", "Questão"]
```

Se seus cartões utilizam outros nomes de campos, você pode personalizar a lista. 

Por exemplo:
  ```
"FIELDS_TO_CHECK": ["Pergunta", "Definição"]
```

Neste exemplo, o add-on verificará os campos "Pergunta" e "Definição" para realizar a análise de similaridade.

**Observações**: O nome dos campos é sensível a maiúsculas e minúsculas (case-sensitive). Certifique-se de que os nomes dos campos no arquivo de configuração correspondam exatamente aos nomes dos campos nos seus cartões.

### GROUP_SIZE

**Descrição**: Define o tamanho dos grupos de cartões com base no número de caracteres presentes no texto. O AnkiFuzzy agrupa os cartões por tamanhos semelhantes para otimizar a comparação de similaridade.

**Exemplo**:
```
"GROUP_SIZE": 40
```

No exemplo acima, os cartões serão agrupados em blocos de 40 caracteres. Cartões com um texto de comprimento entre 0 a 40 caracteres serão comparados entre si, de 41 a 80 em outro grupo, e assim por diante. Se você deseja uma granularidade diferente, ajuste este valor conforme necessário.

**Observações**: Um valor menor de `GROUP_SIZE` resultará em grupos mais precisos, mas pode tornar o processo de comparação mais lento, enquanto um valor maior pode acelerar a análise, mas com menor precisão.

---

#### English (en)

### FIELDS_TO_CHECK

**Description**: A list of fields that AnkiFuzzy checks to find the card content. These fields are used to extract the text from each card for similarity comparison.

**Example**:
```
"FIELDS_TO_CHECK": ["Frente", "Front", "Questão"]
```

If your cards use other field names, you can customize this list. 

For example:
  ```
"FIELDS_TO_CHECK": ["Question", "Definition"]
```

In this example, the add-on will check the "Question" and "Definition" fields for similarity analysis.

**Notes**: Field names are case-sensitive. Make sure the field names in the configuration file exactly match the field names in your cards.

### GROUP_SIZE

**Description**: Defines the size of the groups of cards based on the number of characters present in the text. AnkiFuzzy groups cards by similar sizes to optimize similarity comparisons.

**Example**:
```
"GROUP_SIZE": 40
```

In the example above, cards will be grouped in blocks of 40 characters. Cards with a text length between 0 to 40 characters will be compared with each other, 41 to 80 in another group, and so on. If you want a different level of granularity, adjust this value accordingly.

**Notes**: A smaller `GROUP_SIZE` value will result in more precise groups but may slow down the comparison process, while a larger value can speed up the analysis but with reduced precision.
