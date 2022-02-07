MEMORY
     {
        SDRAM (wx) : ORIGIN = 2147483648, LENGTH = 33554432
     }
 OUTPUT_FORMAT("elf32-littlearm")
_region_min_align = 4;
MEMORY
    {
    FLASH (rx) : ORIGIN = (0x60000000 + 0x0), LENGTH = (8192*1K - 0x0)
    SRAM (wx) : ORIGIN = 0x20200000, LENGTH = (768 * 1K)
   
    ITCM(rw) : ORIGIN = 0, LENGTH = 131072
    DTCM(rw) : ORIGIN = 536870912, LENGTH = 131072
   
   
   
   
   
   
   
   
    IDT_LIST (wx) : ORIGIN = 0xFFFFF7FF, LENGTH = 2K
    }
ENTRY("__start")
SECTIONS
    {
 .rel.plt :
 {
 *(.rel.plt)
 PROVIDE_HIDDEN (__rel_iplt_start = .);
 *(.rel.iplt)
 PROVIDE_HIDDEN (__rel_iplt_end = .);
 }
 .rela.plt :
 {
 *(.rela.plt)
 PROVIDE_HIDDEN (__rela_iplt_start = .);
 *(.rela.iplt)
 PROVIDE_HIDDEN (__rela_iplt_end = .);
 }
 .rel.dyn :
 {
 *(.rel.*)
 }
 .rela.dyn :
 {
 *(.rela.*)
 }
    /DISCARD/ :
 {
 *(.plt)
 }
    /DISCARD/ :
 {
 *(.iplt)
 }
   
 __rom_region_start = (0x60000000 + 0x0);
    rom_start :
 {
. = 0x0;
KEEP(*(.boot_hdr.conf))
. = 0x1000;
KEEP(*(.boot_hdr.ivt))
KEEP(*(.boot_hdr.data))
 KEEP(*(.boot_hdr.dcd_data))
. = 0x2000;
. = ALIGN(4);
. = ALIGN( 1 << ((((4 * 32) <= 4) ? 2 : (((4 * 32) <= 8) ? 3 : (((4 * 32) <= 16) ? 4 : (((4 * 32) <= 32) ? 5 : (((4 * 32) <= 64) ? 6 : (((4 * 32) <= 128) ? 7 : (((4 * 32) <= 256) ? 8 : (((4 * 32) <= 512) ? 9 : (((4 * 32) <= 1024) ? 10 : (((4 * 32) <= 2048) ? 11 : (((4 * 32) <= 4096) ? 12 : (((4 * 32) <= 8192) ? 13 : (((4 * 32) <= 16384) ? 14 : (((4 * 32) <= 32768) ? 15:(((4 * 32) <= 65536) ? 16 : (((4 * 32) <= 131072) ? 17 : (((4 * 32) <= 262144) ? 18:(((4 * 32) <= 524288) ? 19 : (((4 * 32) <= 1048576) ? 20 : (((4 * 32) <= 2097152) ? 21 : (((4 * 32) <= 4194304) ? 22 : (((4 * 32) <= 8388608) ? 23 : (((4 * 32) <= 16777216) ? 24 : (((4 * 32) <= 33554432) ? 25 : (((4 * 32) <= 67108864) ? 26 : (((4 * 32) <= 134217728) ? 27 : (((4 * 32) <= 268435456) ? 28 : (((4 * 32) <= 536870912) ? 29 : (((4 * 32) <= 1073741824) ? 30 : (((4 * 32) <= 2147483648) ? 31 : 32))))))))))))))))))))))))))))))) );
. = ALIGN( 1 << ((((4 * (16 + 160)) <= 4) ? 2 : (((4 * (16 + 160)) <= 8) ? 3 : (((4 * (16 + 160)) <= 16) ? 4 : (((4 * (16 + 160)) <= 32) ? 5 : (((4 * (16 + 160)) <= 64) ? 6 : (((4 * (16 + 160)) <= 128) ? 7 : (((4 * (16 + 160)) <= 256) ? 8 : (((4 * (16 + 160)) <= 512) ? 9 : (((4 * (16 + 160)) <= 1024) ? 10 : (((4 * (16 + 160)) <= 2048) ? 11 : (((4 * (16 + 160)) <= 4096) ? 12 : (((4 * (16 + 160)) <= 8192) ? 13 : (((4 * (16 + 160)) <= 16384) ? 14 : (((4 * (16 + 160)) <= 32768) ? 15:(((4 * (16 + 160)) <= 65536) ? 16 : (((4 * (16 + 160)) <= 131072) ? 17 : (((4 * (16 + 160)) <= 262144) ? 18:(((4 * (16 + 160)) <= 524288) ? 19 : (((4 * (16 + 160)) <= 1048576) ? 20 : (((4 * (16 + 160)) <= 2097152) ? 21 : (((4 * (16 + 160)) <= 4194304) ? 22 : (((4 * (16 + 160)) <= 8388608) ? 23 : (((4 * (16 + 160)) <= 16777216) ? 24 : (((4 * (16 + 160)) <= 33554432) ? 25 : (((4 * (16 + 160)) <= 67108864) ? 26 : (((4 * (16 + 160)) <= 134217728) ? 27 : (((4 * (16 + 160)) <= 268435456) ? 28 : (((4 * (16 + 160)) <= 536870912) ? 29 : (((4 * (16 + 160)) <= 1073741824) ? 30 : (((4 * (16 + 160)) <= 2147483648) ? 31 : 32))))))))))))))))))))))))))))))) );
_vector_start = .;
KEEP(*(.exc_vector_table))
KEEP(*(".exc_vector_table.*"))
KEEP(*(.gnu.linkonce.irq_vector_table*))
KEEP(*(.vectors))
_vector_end = .;
 } > FLASH
    text :
 {
 __text_region_start = .;
 *(.text)
 *(".text.*")
 *(".TEXT.*")
 *(.gnu.linkonce.t.*)
 *(.glue_7t) *(.glue_7) *(.vfp11_veneer) *(.v4_bx)
 } > FLASH
 __text_region_end = .;
 .ARM.extab :
 {
 *(.ARM.extab* .gnu.linkonce.armextab.*)
 } > FLASH
 .ARM.exidx :
 {
 __exidx_start = .;
 *(.ARM.exidx* gnu.linkonce.armexidx.*)
 __exidx_end = .;
 } > FLASH
 __rodata_region_start = .;
 initlevel :
 {
  __init_start = .;
  __init_PRE_KERNEL_1_start = .; KEEP(*(SORT(.z_init_PRE_KERNEL_1[0-9]_*))); KEEP(*(SORT(.z_init_PRE_KERNEL_1[1-9][0-9]_*)));
  __init_PRE_KERNEL_2_start = .; KEEP(*(SORT(.z_init_PRE_KERNEL_2[0-9]_*))); KEEP(*(SORT(.z_init_PRE_KERNEL_2[1-9][0-9]_*)));
  __init_POST_KERNEL_start = .; KEEP(*(SORT(.z_init_POST_KERNEL[0-9]_*))); KEEP(*(SORT(.z_init_POST_KERNEL[1-9][0-9]_*)));
  __init_APPLICATION_start = .; KEEP(*(SORT(.z_init_APPLICATION[0-9]_*))); KEEP(*(SORT(.z_init_APPLICATION[1-9][0-9]_*)));
  __init_SMP_start = .; KEEP(*(SORT(.z_init_SMP[0-9]_*))); KEEP(*(SORT(.z_init_SMP[1-9][0-9]_*)));
  __init_end = .;
 } > FLASH
 devices :
 {
  __device_start = .;
  __device_PRE_KERNEL_1_start = .; KEEP(*(SORT(.z_device_PRE_KERNEL_1[0-9]_*))); KEEP(*(SORT(.z_device_PRE_KERNEL_1[1-9][0-9]_*)));
  __device_PRE_KERNEL_2_start = .; KEEP(*(SORT(.z_device_PRE_KERNEL_2[0-9]_*))); KEEP(*(SORT(.z_device_PRE_KERNEL_2[1-9][0-9]_*)));
  __device_POST_KERNEL_start = .; KEEP(*(SORT(.z_device_POST_KERNEL[0-9]_*))); KEEP(*(SORT(.z_device_POST_KERNEL[1-9][0-9]_*)));
  __device_APPLICATION_start = .; KEEP(*(SORT(.z_device_APPLICATION[0-9]_*))); KEEP(*(SORT(.z_device_APPLICATION[1-9][0-9]_*)));
  __device_SMP_start = .; KEEP(*(SORT(.z_device_SMP[0-9]_*))); KEEP(*(SORT(.z_device_SMP[1-9][0-9]_*)));
  __device_end = .;
 } > FLASH
 sw_isr_table :
 {
  . = ALIGN(0);
  *(.gnu.linkonce.sw_isr_table*)
 } > FLASH
 initlevel_error :
 {
  KEEP(*(SORT(.z_init_[_A-Z0-9]*)))
 }
 ASSERT(SIZEOF(initlevel_error) == 0, "Undefined initialization levels used.")
 ctors :
 {
  . = ALIGN(4);
  __CTOR_LIST__ = .;
  LONG((__CTOR_END__ - __CTOR_LIST__) / 4 - 2)
  KEEP(*(SORT_BY_NAME(".ctors*")))
  LONG(0)
  __CTOR_END__ = .;
 } > FLASH
 init_array :
 {
  . = ALIGN(4);
  __init_array_start = .;
  KEEP(*(SORT_BY_NAME(".init_array*")))
  __init_array_end = .;
 } > FLASH
 app_shmem_regions :
 {
  __app_shmem_regions_start = .;
  KEEP(*(SORT(.app_regions.*)));
  __app_shmem_regions_end = .;
 } > FLASH
 bt_l2cap_fixed_chan_area : SUBALIGN(4) { _bt_l2cap_fixed_chan_list_start = .; KEEP(*(SORT_BY_NAME(._bt_l2cap_fixed_chan.static.*))); _bt_l2cap_fixed_chan_list_end = .; } > FLASH
 bt_gatt_service_static_area : SUBALIGN(4) { _bt_gatt_service_static_list_start = .; KEEP(*(SORT_BY_NAME(._bt_gatt_service_static.static.*))); _bt_gatt_service_static_list_end = .; } > FLASH
 k_p4wq_initparam_area : SUBALIGN(4) { _k_p4wq_initparam_list_start = .; KEEP(*(SORT_BY_NAME(._k_p4wq_initparam.static.*))); _k_p4wq_initparam_list_end = .; } > FLASH
 log_strings_sections :
 {
  __log_strings_start = .;
  KEEP(*(SORT(.log_strings*)));
  __log_strings_end = .;
 } > FLASH
 log_const_sections :
 {
  __log_const_start = .;
  KEEP(*(SORT(.log_const_*)));
  __log_const_end = .;
 } > FLASH
 log_backends_sections :
 {
  __log_backends_start = .;
  KEEP(*("._log_backend.*"));
  __log_backends_end = .;
 } > FLASH
 shell_area : SUBALIGN(4) { _shell_list_start = .; KEEP(*(SORT_BY_NAME(._shell.static.*))); _shell_list_end = .; } > FLASH
 shell_root_cmds_sections :
 {
  __shell_root_cmds_start = .;
  KEEP(*(SORT(.shell_root_cmd_*)));
  __shell_root_cmds_end = .;
 } > FLASH
 font_entry_sections :
 {
  __font_entry_start = .;
  KEEP(*(SORT_BY_NAME("._cfb_font.*")))
  __font_entry_end = .;
 } > FLASH
 tracing_backend_area : SUBALIGN(4) { _tracing_backend_list_start = .; KEEP(*(SORT_BY_NAME(._tracing_backend.static.*))); _tracing_backend_list_end = .; } > FLASH
 zephyr_dbg_info :
 {
  KEEP(*(".dbg_thread_info"));
 } > FLASH
 device_handles :
 {
  __device_handles_start = .;
  KEEP(*(SORT(.__device_handles_pass2*)));
  __device_handles_end = .;
 } > FLASH
    rodata :
 {
 *(.rodata)
 *(".rodata.*")
 *(.gnu.linkonce.r.*)
 . = ALIGN(4);
 } > FLASH
 .gcc_except_table : ONLY_IF_RO
 {
 *(.gcc_except_table .gcc_except_table.*)
 } > FLASH
 __rodata_region_end = .;
 . = ALIGN(_region_min_align);
 __rom_region_end = .;



 .got :
 {
   . = ALIGN(4);
   *(.got.plt)
   *(.igot.plt)
   *(.got)
   *(.igot)
 } > FLASH

 .swift5 :
 {
   . = ALIGN(4);
   __start_swift5_protocols = .;
   *(swift5_protocols*)
   __stop_swift5_protocols = .;
   
   . = ALIGN(4);
   __start_swift5_protocol_conformances = .;
   *(swift5_protocol_conformances*)
   __stop_swift5_protocol_conformances = .;

   . = ALIGN(4);
   __start_swift5_type_metadata = .;
   *(swift5_type_metadata*)
   __stop_swift5_type_metadata = .;

   . = ALIGN(4);
   __start_swift5_typeref = .;
   *(swift5_typeref*)
   __stop_swift5_typeref = .;

   . = ALIGN(4);
   __start_swift5_reflstr = .;
   *(swift5_reflstr)
   __stop_swift5_reflstr = .;

   . = ALIGN(4);
   __start_swift5_fieldmd = .;
   *(swift5_fieldmd)
   __stop_swift5_fieldmd = .;

   . = ALIGN(4);
   __start_swift5_assocty = .;
   *(swift5_assocty)
   __stop_swift5_assocty = .;

   . = ALIGN(4);
   __start_swift5_replace = .;
   *(swift5_replace)
   __stop_swift5_replace = .;

   . = ALIGN(4);
   __start_swift5_replac2 = .;
   *(swift5_replac2)
   __stop_swift5_replac2 = .;

   . = ALIGN(4);
   __start_swift5_builtin = .;
   *(swift5_builtin)
   __stop_swift5_builtin = .;

   . = ALIGN(4);
   __start_swift5_capture = .;
   *(swift5_capture)
   __stop_swift5_capture = .;
 } > FLASH
 

 _image_rodata_end = .;
 . = ALIGN(_region_min_align);
 _image_rom_end = .;




   
 . = 0x20200000;
 . = ALIGN(_region_min_align);
 _image_ram_start = .;
.ramfunc :
{
 . = ALIGN(_region_min_align);
 __ramfunc_start = .;
 *(.ramfunc)
 *(".ramfunc.*")
 . = ALIGN(_region_min_align);
 __ramfunc_end = .;
} > SRAM AT > FLASH
__ramfunc_size = __ramfunc_end - __ramfunc_start;
__ramfunc_load_start = LOADADDR(.ramfunc);
   
    datas :
 {
 __data_region_start = .;
 __data_start = .;
 *(.data)
 *(".data.*")
 *(".kernel.*")
 __data_end = .;
 } > SRAM AT > FLASH
    __data_size = __data_end - __data_start;
    __data_load_start = LOADADDR(datas);
    __data_region_load_start = LOADADDR(datas);
        device_states :
        {
                __device_states_start = .;
  KEEP(*(".z_devstate"));
  KEEP(*(".z_devstate.*"));
                __device_states_end = .;
        } > SRAM AT > FLASH
 initshell :
 {
  __shell_module_start = .;
  KEEP(*(".shell_module_*"));
  __shell_module_end = .;
  __shell_cmd_start = .;
  KEEP(*(".shell_cmd_*"));
  __shell_cmd_end = .;
 } > SRAM AT > FLASH
 log_dynamic_sections :
 {
  __log_dynamic_start = .;
  KEEP(*(SORT(.log_dynamic_*)));
  __log_dynamic_end = .;
 } > SRAM AT > FLASH
 _static_thread_data_area : SUBALIGN(4) { __static_thread_data_list_start = .; KEEP(*(SORT_BY_NAME(.__static_thread_data.static.*))); __static_thread_data_list_end = .; } > SRAM AT > FLASH
 k_timer_area : SUBALIGN(4) { _k_timer_list_start = .; *(SORT_BY_NAME(._k_timer.static.*)); _k_timer_list_end = .; } > SRAM AT > FLASH
 k_mem_slab_area : SUBALIGN(4) { _k_mem_slab_list_start = .; *(SORT_BY_NAME(._k_mem_slab.static.*)); _k_mem_slab_list_end = .; } > SRAM AT > FLASH
 k_mem_pool_area : SUBALIGN(4) { _k_mem_pool_list_start = .; *(SORT_BY_NAME(._k_mem_pool.static.*)); _k_mem_pool_list_end = .; } > SRAM AT > FLASH
 k_heap_area : SUBALIGN(4) { _k_heap_list_start = .; *(SORT_BY_NAME(._k_heap.static.*)); _k_heap_list_end = .; } > SRAM AT > FLASH
 k_mutex_area : SUBALIGN(4) { _k_mutex_list_start = .; *(SORT_BY_NAME(._k_mutex.static.*)); _k_mutex_list_end = .; } > SRAM AT > FLASH
 k_stack_area : SUBALIGN(4) { _k_stack_list_start = .; *(SORT_BY_NAME(._k_stack.static.*)); _k_stack_list_end = .; } > SRAM AT > FLASH
 k_msgq_area : SUBALIGN(4) { _k_msgq_list_start = .; *(SORT_BY_NAME(._k_msgq.static.*)); _k_msgq_list_end = .; } > SRAM AT > FLASH
 k_mbox_area : SUBALIGN(4) { _k_mbox_list_start = .; *(SORT_BY_NAME(._k_mbox.static.*)); _k_mbox_list_end = .; } > SRAM AT > FLASH
 k_pipe_area : SUBALIGN(4) { _k_pipe_list_start = .; *(SORT_BY_NAME(._k_pipe.static.*)); _k_pipe_list_end = .; } > SRAM AT > FLASH
 k_sem_area : SUBALIGN(4) { _k_sem_list_start = .; *(SORT_BY_NAME(._k_sem.static.*)); _k_sem_list_end = .; } > SRAM AT > FLASH
 k_queue_area : SUBALIGN(4) { _k_queue_list_start = .; *(SORT_BY_NAME(._k_queue.static.*)); _k_queue_list_end = .; } > SRAM AT > FLASH
 k_condvar_area : SUBALIGN(4) { _k_condvar_list_start = .; *(SORT_BY_NAME(._k_condvar.static.*)); _k_condvar_list_end = .; } > SRAM AT > FLASH
 _net_buf_pool_area : SUBALIGN(4)
 {
  _net_buf_pool_list = .;
  KEEP(*(SORT_BY_NAME("._net_buf_pool.static.*")))
 } > SRAM AT > FLASH
 .gcc_except_table : ONLY_IF_RW
 {
 *(.gcc_except_table .gcc_except_table.*)
 } > SRAM AT > FLASH
    __data_region_end = .;
   bss (NOLOAD) :
 {
        . = ALIGN(4);
 __bss_start = .;
 __kernel_ram_start = .;
 *(.bss)
 *(".bss.*")
 *(COMMON)
 *(".kernel_bss.*")
 __bss_end = ALIGN(4);
 } > SRAM AT > SRAM
    noinit (NOLOAD) :
        {
        *(.noinit)
        *(".noinit.*")
 *(".kernel_noinit.*")
        } > SRAM
    _image_ram_end = .;
    _end = .;
    __kernel_ram_end = 0x20200000 + (768 * 1K);
    __kernel_ram_size = __kernel_ram_end - __kernel_ram_start;
   

 .itcm : SUBALIGN(4)
 {
  __itcm_start = .;
  *(.itcm)
  *(".itcm.*")
  __itcm_end = .;
 } > ITCM AT> FLASH
 __itcm_size = __itcm_end - __itcm_start;
 __itcm_load_start = LOADADDR(.itcm);


 .dtcm_bss (NOLOAD) : SUBALIGN(4)
 {
  __dtcm_start = .;
  __dtcm_bss_start = .;
  *(.dtcm_bss)
  *(".dtcm_bss.*")
  __dtcm_bss_end = .;
 } > DTCM
 .dtcm_noinit (NOLOAD) : SUBALIGN(4)
 {
  __dtcm_noinit_start = .;
  *(.dtcm_noinit)
  *(".dtcm_noinit.*")
  __dtcm_noinit_end = .;
 } > DTCM
 .dtcm_data : SUBALIGN(4)
 {
  __dtcm_data_start = .;
  *(.dtcm_data)
  *(".dtcm_data.*")
  __dtcm_data_end = .;
 } > DTCM AT> FLASH
 __dtcm_end = .;
 __dtcm_data_load_start = LOADADDR(.dtcm_data);

/DISCARD/ :
{
 KEEP(*(.irq_info*))
 KEEP(*(.intList*))
}
 .stab 0 : { *(.stab) }
 .stabstr 0 : { *(.stabstr) }
 .stab.excl 0 : { *(.stab.excl) }
 .stab.exclstr 0 : { *(.stab.exclstr) }
 .stab.index 0 : { *(.stab.index) }
 .stab.indexstr 0 : { *(.stab.indexstr) }
 .gnu.build.attributes 0 : { *(.gnu.build.attributes .gnu.build.attributes.*) }
 .comment 0 : { *(.comment) }
 .debug 0 : { *(.debug) }
 .line 0 : { *(.line) }
 .debug_srcinfo 0 : { *(.debug_srcinfo) }
 .debug_sfnames 0 : { *(.debug_sfnames) }
 .debug_aranges 0 : { *(.debug_aranges) }
 .debug_pubnames 0 : { *(.debug_pubnames) }
 .debug_info 0 : { *(.debug_info .gnu.linkonce.wi.*) }
 .debug_abbrev 0 : { *(.debug_abbrev) }
 .debug_line 0 : { *(.debug_line .debug_line.* .debug_line_end ) }
 .debug_frame 0 : { *(.debug_frame) }
 .debug_str 0 : { *(.debug_str) }
 .debug_loc 0 : { *(.debug_loc) }
 .debug_macinfo 0 : { *(.debug_macinfo) }
 .debug_weaknames 0 : { *(.debug_weaknames) }
 .debug_funcnames 0 : { *(.debug_funcnames) }
 .debug_typenames 0 : { *(.debug_typenames) }
 .debug_varnames 0 : { *(.debug_varnames) }
 .debug_pubtypes 0 : { *(.debug_pubtypes) }
 .debug_ranges 0 : { *(.debug_ranges) }
 .debug_macro 0 : { *(.debug_macro) }
    /DISCARD/ : { *(.note.GNU-stack) }
    .ARM.attributes 0 :
 {
 KEEP(*(.ARM.attributes))
 KEEP(*(.gnu.attributes))
 }
.last_section (NOLOAD) :
{
} > FLASH
_flash_used = LOADADDR(.last_section) - __rom_region_start;
    }
