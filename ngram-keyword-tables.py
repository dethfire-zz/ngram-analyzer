import streamlit as st
import nltk
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
from nltk.util import ngrams
import requests
import json
import pandas as pd

def extract_ngrams(data, num):
  n_grams = ngrams(nltk.word_tokenize(data), num)
  gram_list = [ ' '.join(grams) for grams in n_grams]

  query_tokens = nltk.pos_tag(gram_list)
  query_tokens = [x for x in query_tokens if x[1] in ['NN','NNS','NNP','NNPS','VBG','VBN']]
  query_tokens = [x[0] for x in query_tokens]

  return query_tokens

def surfer(entities):
  entities_type = [x[2] for x in entities]
  entities = [x[0] for x in entities]
  keywords = json.dumps(entities)

  url2 = 'https://db2.keywordsur.fr/keyword_surfer_keywords?country=us&keywords=' + keywords
  response2 = requests.get(url2,verify=True)
  volume = json.loads(response2.text)

  d = {'Keyword': [], 'Volume': [], 'CPC':[], 'Competition':[], 'Entity Types':[]}
  df = pd.DataFrame(data=d)
  counter=0

  for word in volume:

    if volume[word]["cpc"] == '':
      volume[word]["cpc"] = 0.0
    
    if volume[word]["competition"] == '':
      volume[word]["competition"] = 0.0

    #print(volume[word]["cpc"])
    #print(volume[word]["competition"])

    new = {"Keyword":word,"Volume":str(volume[word]["search_volume"]),"CPC":"$"+str(round(float(volume[word]["cpc"]),2)),"Competition":str(round(float(volume[word]["competition"]),4)),'Entity Types':entities_type[counter]}
    df = df.append(new, ignore_index=True)
    counter +=1

  df.style.set_properties(**{'text-align': 'left'})
  df.sort_values(by=['Volume'], ascending=True)
  
  return df

def kg(keywords):

  kg_entities = []
  apikey = st.secrets["apikey"]

  for x in keywords:
    url = f'https://kgsearch.googleapis.com/v1/entities:search?query={x}&key={apikey}&limit=1&indent=True'
    payload = {}
    headers= {}
    response = requests.request("GET", url, headers=headers, data = payload)
    data = json.loads(response.text)
    #print(data)

    try:
      getlabel = data['itemListElement'][0]['result']['@type']
      score = round(float(data['itemListElement'][0]['resultScore']))
    except:
      score = 0
      getlabel = ['none']

    labels = ""
    
    for item in getlabel:
      labels += item + ","
    labels = labels[:-1].replace(",",", ")
    
    if labels != ['none'] and score > 500:
      kg_subset = []
      kg_subset.append(x)
      kg_subset.append(score)
      kg_subset.append(labels)
      #print(kg_subset)

      kg_entities.append(kg_subset)
      
  return kg_entities

st.markdown("""
<style>
.big-font {
    font-size:50px !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<p class="big-font">N-Gram Text Anayzer</p>
<p>Pull out 1,2,3 gram portions of text. Detect if an entity. Find volume, cpc, competition score.</p>
<b>Directions: </b></ br><ol>
<li>Copy and paste in text, click process. Not recommended to run with very long text (+1000 words) or your browser may catch fire. Works best with paragraphs.</li>
</ol>
""", unsafe_allow_html=True)

with st.form("data"):
    data = st.text_area(label="Your Text Data")
    submitted = st.form_submit_button("Process")
    if submitted:
        data = data.replace('\\','')
        data = data.replace(',','')
        data = data.replace('.','')
        data = data.replace(';','')
        
        i=1
        while i<4:
            
            if i == 1:
                gram = "Unigram"
            elif i == 2:
                gram = "Bigram"
            elif i ==3:
                gram = "Trigram"
                
            st.write(":sunglasses: Processing " + gram + "...")
            keywords = extract_ngrams(data, i)
            entities = kg(keywords)
            df = surfer(entities)
            

            st.title(gram + " Entity Table")
            st.dataframe(df)
            i+=1

st.write('Author: [Greg Bernhardt](https://twitter.com/GregBernhardt4) | Friends: [Rocket Clicks](https://www.rocketclicks.com) and [Physics Forums](https://www.physicsforums.com)')
