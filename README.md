Rozšíření genetického algoritmu na problém, který nepracuje s binárním řetězcem ale spojitým vektorem

Porovnání variant Genetického algoritmu s něčím z Matematické informatiky

výběr 3 testovacích funkcí (např. Schweffel)
nachystat si to abych do té funkce jenom hodil algoritmus (modulárně) protože budeme používat dál

1. IEEE-754 https://www.h-schmidt.net/FloatConverter/IEEE754.html https://nextcloud.hrubos.dev/apps/files/files/17099?dir=%2FOneDrive%2FApps%2Fremotely-save%2FVUT%2F1.%20ro%C4%8Dn%C3%ADk%20letn%C3%AD%20semestr%2FISU&editing=false&openfile=true
    - převod float čísla pomocí knihovny na bity
    - na to použiju už připravený geneťák z cvičení 1
    - mapuju na nějaký interval a potom musím kontrolovat jestli je v tom rozsahu (různé strategie vracení na hranici)
    - často poleze mimo definovaný rozsah
1. FPR - fixed point representation
    - stejně - vezmu float a věnuju nějaké bity celé části a některé desetinné části
    - musí být stejně veliké (32b)
    - použiju 10 bitů abych dostal rozsah [-500;500] (2^10 je 1024 takže 1001 čísel se vleze !ale budu mít 23 hodnot které nejsou namapované! - zase můžu prostě zastavit na hranici pokud bude vyšší jak 1001?), můžu transformovat na [0;1001]
    - zbytek bitů na decimal část (22 bitů)
1. BCD - binary coded decimal
    - zase transformuju na [0;1001]
    - pro každý řád si určím kolik bitů ho reprezentuje
    - např. 4 bity na každý řád (0...9 - potřebuju minimálně 4 bity)
    - tzn. budu mít 16b na celou část 16b na decimal část
    - klesá přesnost na desetinné části

TYHLE VÝSLEDNÉ ČÍSLA (REPREZENTOVANÉ JAKO 32b ČÍSLA) NARVU DO EXISTUJÍCÍHO GENEŤÁKU

potom předělám geneťák aby fungoval s reálnýma číslama
Real-valued GA
1. křížení
    - kombinuju stejně jako v bin. ale když se kříží tak se prohazují celá čísla (tzn. r1=[2,34;-7,12;0,22], r2=[1,11;0,07;19,17] p1=[2,34;0,07;19,17])
    - prostě křížím na úrovni dimenzí
1. mutace
    - náhoda: s nízkou pravděpodobností vegeneruju nové random číslo (z povoleného rozsahu) v jedné dimenzi - pravděpodobnost mutace by měla být malá aby se to nesklouzlo k random searchi
    - náhoda ale generuju s normálním rozložením se středem v původní hodnotě - vpodstatě local search
        - přidává nový parametr rozptyl (nastaví uživatel e.g. já)
        - pozor! může vygenerovat cokoliv takže ošetřovat


obě metody (3x + 2x variace) otestuji na nějakých funkcích na 10 běhů a porovnat mezi sebou na základě !!!konvergenční křivky!!!
najít nejlepší parametry, ty potom odevzdat
zahrnout názor proč něco funguje/nefunguje
