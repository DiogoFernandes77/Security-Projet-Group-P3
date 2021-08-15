# Security Projet Group P3

## Members 
85097 - Dany Costa
89221 - Diogo Fernandes 
88861 - Pedro Alves
84760 - Sérgio Gasalho

## Distribuir Peças
[	[Dany]Neste momento é preciso alterar a distribuição para que o baralho seja enviado de jogador para jogador para isso : 
	- enviar a lista de conexões inicialmente pelo Server para o primeiro utilizador e fazer respetivamente uma função que baralhe a ordem ( isto fica para o fim ) 
	- em cada utilizador é preciso criar uma função que baralhe o baralho antes de o enviar para o próximo utilizador. 
	- na fase de escolha deve-se de implementar também a possibilidade de não escolher nenhuma peça (isto é tudo feito dentro da classe do player quando a ação é escolher peça) 
	- rever melhor a questão da interação server-cliente e fazer com que as ações sejam mais independentes no client e só depois é que envia os dados para o server(ou cliente). 
		Por exemplo: Quando o utilizador estiver a efetuar a ação da escolha de peça a unica informação (data) que ele vai enviar ( para o proximo utilizador) é o baralho por isso deve-se de dar a possiblidade ao utilizador de:
			-escolher peça 
			-não escolher peça 
				- trocar de peça (uma ou mais) 
				- não fazer nada.
----Nota: este tipo de filosofia aplica-se também para o jogo !
]
-o primeiro jogador recebe todas as 28 peças do Deck em plain text
-depois encripta-as separadamente (com a sua chave privada) e envia-as para o jogador seguinte
-o segundo recebe, encripta (tambem com a sua chave privada) e envia para outro jogador e assim sucessivamente

-depois dos 4 jogadores fazerem isso, o primeiro volta a receber o Deck
-a partir deste momento, o Deck vai ser passado de jogador em jogador de forma aleatória, tendo cada um sempre duas opções:
-tirar uma peça do Deck (20%, por exemplo)
-não tirar peça (100-20=80%, por exemplo) e neste caso passa a ter mais duas opções:
-trocar de peças, uma ou mais (volta a colocar peça(s) no Deck e tira outra(s))
-não faz nada
-depois de ter tomado as suas decisões, o jogador volta a baralhar todas as peças que restam no Deck
-este jogador envia as peças restantes no Deck (cifradas e baralhadas) para um dos outros jogadores (aleatório)
-isto repete-se até todos jogadores terem 7 peças (ainda cifradas e ninguém sabe as peças de ninguém, nem a mesa (TableManager))
-depois, cada jogador tem de criar um bit_commitment (hash function (qualquer) aplicada ao conjunto das suas peças ainda cifradas)
-o bit_commitment também tem de ser assinado pelo jogador
-quando este processo estiver concluido, os jogadores partilham as suas chaves públicas para que cada um deles possa decifrar as suas peças

--bit_commitment:
(o que ouvi da aula):
[na parte do bit commitment pelo que o stor teve a dizer na aula é basicamente o jogador "assinar" a mão antes de saber os valores das peças 
não é suposto o jogador saber o valor das peças quando esta a escolher ! 
e impossivel fazer um bit comitment a umas peças q nao se conhece]

-permite que em quaquer momento do jogo o jogador possa provar quais eram as suas peças
-caso algum jogador detecte batota, é possivel calcular novamente o bit_commitment e e descobrir o responsável
-caso tenha ocorrido batota e ambos os jogadores conseguirem provar que nao fizeram batota, a culpa será do jogador que recebeu as peças para as cifrar pela primeira vez (único a ter acesso ao Deck antes de ser cifrado)
