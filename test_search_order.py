import json
from src.web_search_feature import WebSearchFeature

config = json.load(open('config/search_config.json'))['web_search']

print('=== Configuration ===')
print(f'Method: {config["search_method"]}')
print(f'Engine: {config["search_engine"]}')
print(f'Fallback to HTML: {config.get("fallback_to_html", False)}')
print(f'Fallback to Google: {config.get("fallback_to_google", False)}')

print('\n=== Testing Search (Bing ONLY) ===')
feature = WebSearchFeature(config)
result = feature.search_web('python tutorial', max_results=2)

print(f'\nSuccess: {result["success"]}')
print(f'Results: {result["result_count"]}')
if result.get("results"):
    print(f'Source: {result["results"][0]["source"]}')
    print('\nResult titles:')
    for i, r in enumerate(result["results"]):
        try:
            print(f'{i+1}. {r["title"][:50]}')
        except:
            print(f'{i+1}. (title encoding issue)')
else:
    print('No results - Bing might be showing CAPTCHA or blocked')

feature.close()
