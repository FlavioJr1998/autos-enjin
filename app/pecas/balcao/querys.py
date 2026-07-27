def retorna_contatos_abertos( data_hoje, revendas ):
  ## O OBJETIVO É RETORNAR OS CONTATOS ABERTOS DAS REVENDAS INFORMADAS
    query = f"""
SELECT cco.revenda                                AS Revenda,
       gerv.cidade                                AS Cidade,
       cco.contato                                AS Contato,
       ate.vendedor                               AS Cod_Vendedor,
       usu.nome                                   AS Nome_Vendedor,
       COUNT(DISTINCT pir.item_estoque)           AS QTD_Itens, -- Agrupa e conta a quantidade de itens únicos do contato
       cco.situacao                               AS Situacao_Contato,
       cli.cliente                                AS Cod_Cliente,
       cli.nome                                   AS Nome_Cliente,
       tpt.des_tipo_transacao                     AS Desc_Tipo_Transacao,
       cco.dta_contato                            AS Data_Contato,
       TRUNC(TO_DATE('{data_hoje}', 'dd/mm/yyyy')) - TRUNC(cco.dta_contato) AS Dias_Aberto_Contato
  FROM pec_peca_balcao ppb
 INNER JOIN pec_item_relacao pir 
    ON pir.empresa = ppb.empresa 
   AND pir.item_estoque = ppb.item_estoque
  LEFT OUTER JOIN pec_item_estoque pie
    ON pir.empresa = pie.empresa
   AND pir.item_estoque = pie.item_estoque
  LEFT OUTER JOIN cac_contato cco
    ON ppb.empresa = cco.empresa
   AND ppb.revenda = cco.revenda
   AND ppb.atende_balcao = cco.contato
  LEFT OUTER JOIN ger_usuario usu
    ON cco.usuario_abriu = usu.usuario
  LEFT OUTER JOIN fat_cliente cli
    ON cco.cliente = cli.cliente
  LEFT OUTER JOIN fat_tipo_transacao tpt
    ON ppb.tipo_transacao = tpt.tipo_transacao
  LEFT OUTER JOIN ofi_atendimento ate
    ON ppb.empresa = ate.empresa
   AND ppb.revenda = ate.revenda
   AND ppb.atende_balcao = ate.contato
  LEFT OUTER JOIN pec_item_revenda rev
    ON rev.empresa = ppb.empresa
   AND rev.revenda = ppb.revenda
   AND rev.item_estoque = ppb.item_estoque
  LEFT JOIN for_auto_busca_pedido fap
    ON cco.empresa = fap.empresa
   AND cco.revenda = fap.revenda
   AND cco.order_id_auto_busca = fap.order_id
    inner join ger_revenda gerv
on ( cco.empresa = gerv.empresa
   and cco.revenda = gerv.revenda )
 WHERE ppb.empresa = 1
   AND ppb.revenda IN ({revendas})
   AND cco.situacao <> 'F'
 GROUP BY cco.empresa,
          cco.revenda,
          gerv.cidade,
          cco.contato,
          ate.vendedor,
          usu.nome,
          cco.situacao,
          cli.cliente,
          cli.nome,
          tpt.des_tipo_transacao,
          cco.dta_contato
 ORDER BY cco.contato
    """
    return query